from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsProductOwner
from apps.prioritization.models import Assessment
from apps.requests import serializers
from apps.requests.models import TRANSITIONS, Category, Status
from apps.requests.services import (
    bump_version,
    create_request,
    get_request,
    lock_request,
    normalise_tags,
    requests_for,
    workspace_id_of,
)

DATE_WINDOWS = {"7d": 7, "30d": 30, "90d": 90}
REQUIRED = "This field is required."


class CategoryListView(APIView):
    def get(self, request: Request) -> Response:
        categories = Category.objects.filter(workspace_id=workspace_id_of(request.user))
        return Response([{"id": c.id, "name": c.name} for c in categories])


class RequestListView(GenericAPIView):
    """GET lista com filtros (WF-01, WF-04) · POST submete um pedido (WF-02)."""

    def get(self, request: Request) -> Response:
        params = request.query_params
        queryset = requests_for(request.user)
        if search := params.get("search", "").strip():
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(tags__name__icontains=search.lstrip("#"))
            ).distinct()
        if (wanted := params.get("status")) in Status.values:
            queryset = queryset.filter(status=wanted)
        if (category := params.get("category", "")).isdigit():
            queryset = queryset.filter(category_id=int(category))
        if days := DATE_WINDOWS.get(params.get("date", "")):
            queryset = queryset.filter(created_at__gte=timezone.now() - timedelta(days=days))
        if params.get("mine") == "1":
            queryset = queryset.filter(Q(author=request.user) | Q(voted=True))
        queryset = queryset.order_by("-vote_count", "-created_at", "-id")
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(
            [serializers.summary(item, request.user) for item in page]
        )

    def post(self, request: Request) -> Response:
        data = request.data
        title = str(data.get("title") or "").strip()
        description = str(data.get("description") or "").strip()
        tags = data.get("tags") or []
        errors: dict[str, list[str]] = {}
        if not title:
            errors["title"] = [REQUIRED]
        elif len(title) > 200:
            errors["title"] = ["Use at most 200 characters."]
        if not description:
            errors["description"] = [REQUIRED]
        category = None
        if data.get("category") in (None, ""):
            errors["category"] = [REQUIRED]
        else:
            category = Category.objects.filter(
                workspace_id=workspace_id_of(request.user), pk=_int(data.get("category"))
            ).first()
            if category is None:
                errors["category"] = ["Choose a category from the list."]
        if not isinstance(tags, list):
            errors["tags"] = ["Send tags as a list."]
        elif len(normalise_tags(tags)) > 8:
            errors["tags"] = ["Use at most 8 tags."]
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        item = create_request(
            author=request.user,
            title=title,
            description=description,
            category=category,
            tags=tags,
            importance=str(data.get("importance") or "").strip(),
        )
        return Response(
            serializers.detail(get_request(request.user, item.pk), request.user),
            status=status.HTTP_201_CREATED,
        )


class SimilarRequestsView(APIView):
    """Pedidos parecidos com o título/tags que o cliente está a escrever (UC-01, passo 4)."""

    def get(self, request: Request) -> Response:
        words = {w for w in request.query_params.get("q", "").lower().split() if len(w) >= 3}
        tags = set(normalise_tags(request.query_params.get("tags", "").split(",")))
        if not words and not tags:
            return Response([])
        match = Q(tags__name__in=tags)
        for word in words:
            match |= Q(title__icontains=word)
        candidates = list(requests_for(request.user).filter(match).distinct()[:50])

        def relevance(item) -> int:
            title = item.title.lower()
            hits = sum(1 for word in words if word in title)
            return hits + len(tags & {tag.name for tag in item.tags.all()})

        candidates.sort(key=lambda item: (-relevance(item), -item.vote_count, item.id))
        return Response([serializers.summary(item, request.user) for item in candidates[:3]])


class RequestDetailView(APIView):
    def get(self, request: Request, pk: int) -> Response:
        return Response(serializers.detail(get_request(request.user, pk), request.user))


class AssessmentView(APIView):
    """PATCH — o PO avalia impacto/esforço e muda o estado (WF-03, UC-10)."""

    permission_classes = [IsProductOwner]

    @transaction.atomic
    def patch(self, request: Request, pk: int) -> Response:
        item = lock_request(request.user, pk)
        data = request.data
        errors: dict[str, list[str]] = {}
        version = _int(data.get("version"))
        if version is None:
            errors["version"] = [REQUIRED]
        assessment, _ = Assessment.objects.get_or_create(request=item)
        changes: list[str] = []
        estimate: list[str] = []
        for field, low, high, label in (
            ("impact", 1, 5, "impact {}"),
            ("effort", 1, 1000, "effort {} pts"),
        ):
            if field not in data:
                continue
            value = data[field]
            if value is not None:
                value = _int(value)
                if value is None or not low <= value <= high:
                    errors[field] = [f"Use a whole number from {low} to {high}."]
                    continue
            if value != getattr(assessment, field):
                setattr(assessment, field, value)
                estimate.append(label.format(value) if value is not None else f"{field} cleared")
        new_status = data.get("status")
        if new_status not in (None, "", item.status):
            if new_status not in TRANSITIONS[item.status]:
                allowed = ", ".join(Status(s).label for s in TRANSITIONS[item.status]) or "none"
                errors["status"] = [
                    f"A request that is {item.get_status_display()} can only move to: {allowed}."
                ]
            else:
                item.status = new_status
                changes.append(f"Status → {Status(new_status).label}")
        if errors:
            transaction.set_rollback(True)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        if version != item.version:
            transaction.set_rollback(True)
            return Response(
                {
                    "detail": "This request was changed by someone else. Reload and try again.",
                    "version": item.version,
                },
                status=status.HTTP_412_PRECONDITION_FAILED,
            )
        if estimate:
            changes.append(", ".join(estimate))
        if changes:
            assessment.updated_by = request.user
            assessment.save()
            item.save(update_fields=["status", "updated_at"])
            bump_version(item, request.user, "; ".join(changes))
        return Response(serializers.detail(get_request(request.user, pk), request.user))


class PublicRoadmapView(APIView):
    """Projeção pública: só campos explicitamente autorizados (título e categoria)."""

    def get(self, request: Request) -> Response:
        columns: dict[str, list[dict]] = {"planned": [], "in_progress": [], "released": []}
        items = (
            requests_for(request.user)
            .filter(status__in=list(columns))
            .order_by("-updated_at", "-id")
        )
        for item in items:
            columns[item.status].append(
                {"id": item.id, "title": item.title, "category": item.category.name}
            )
        return Response(columns)


def _int(value) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None

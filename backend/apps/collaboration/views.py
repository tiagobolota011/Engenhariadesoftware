from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.collaboration.models import Comment, Notification
from apps.collaboration.notifications import notify_decision, notify_mentions
from apps.core.api import payload, text
from apps.core.auth_views import display_name
from apps.core.permissions import IsProductOwner
from apps.requests import serializers
from apps.requests.services import bump_version, get_request, lock_request


class CommentCreateView(APIView):
    @transaction.atomic
    def post(self, request: Request, pk: int) -> Response:
        data = payload(request)
        item = get_request(request.user, pk)
        body = text(data.get("body"))
        if not body:
            return Response(
                {"body": ["Write a comment first."]}, status=status.HTTP_400_BAD_REQUEST
            )
        created = Comment.objects.create(request=item, author=request.user, body=body)
        notify_mentions(created)
        return Response(serializers.comment(created), status=status.HTTP_201_CREATED)


class DecisionView(APIView):
    """O PO marca (POST) ou retira (DELETE) a decisão de um pedido.

    Há no máximo uma decisão por pedido: marcar outro comentário move-a.
    """

    permission_classes = [IsProductOwner]

    @transaction.atomic
    def post(self, request: Request, pk: int, comment_id: int) -> Response:
        item = lock_request(request.user, pk)
        target = get_object_or_404(Comment, pk=comment_id, request=item)
        if not target.is_decision:
            moved = item.comments.filter(is_decision=True).update(is_decision=False)
            target.is_decision = True
            target.save(update_fields=["is_decision"])
            summary = "Decision changed" if moved else "Decision recorded"
            bump_version(item, request.user, summary, public=summary)
            notify_decision(item, request.user)
        return Response(serializers.comment(target))

    @transaction.atomic
    def delete(self, request: Request, pk: int, comment_id: int) -> Response:
        item = lock_request(request.user, pk)
        target = get_object_or_404(Comment, pk=comment_id, request=item)
        if target.is_decision:
            target.is_decision = False
            target.save(update_fields=["is_decision"])
            bump_version(item, request.user, "Decision removed", public="Decision removed")
        return Response(serializers.comment(target))


class MemberListView(APIView):
    """Membros do workspace, para sugerir quem mencionar (@username)."""

    def get(self, request: Request) -> Response:
        users = (
            User.objects.filter(
                membership__workspace_id=request.user.membership.workspace_id, is_active=True
            )
            .select_related("membership")
            .order_by("first_name", "last_name", "username")
        )
        return Response(
            [
                {
                    "username": user.username,
                    "name": display_name(user),
                    "role_label": user.membership.get_role_display(),
                }
                for user in users
            ]
        )


def _notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "kind": n.kind,
        "kind_label": n.get_kind_display(),
        "message": n.message,
        "actor_name": display_name(n.actor) if n.actor else "Former member",
        "request_id": n.request_id,
        "read": n.read_at is not None,
        "created_at": n.created_at.isoformat(),
    }


def _mine(request: Request):
    return Notification.objects.filter(recipient=request.user)


def _unread(request: Request) -> int:
    return _mine(request).filter(read_at__isnull=True).count()


class NotificationListView(APIView):
    """As 50 notificações mais recentes do utilizador (só as não lidas com ?unread=1)."""

    LIMIT = 50

    def get(self, request: Request) -> Response:
        queryset = _mine(request).select_related("actor")
        if request.query_params.get("unread") == "1":
            queryset = queryset.filter(read_at__isnull=True)
        return Response(
            {
                "unread": _unread(request),
                "results": [_notification(n) for n in queryset[: self.LIMIT]],
            }
        )


class UnreadCountView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"unread": _unread(request)})


class NotificationReadView(APIView):
    def post(self, request: Request, pk: int) -> Response:
        # 404 para notificações de outra pessoa: não se revela que existem.
        item = get_object_or_404(_mine(request).select_related("actor"), pk=pk)
        if item.read_at is None:
            item.read_at = timezone.now()
            item.save(update_fields=["read_at"])
        return Response(_notification(item))


class NotificationReadAllView(APIView):
    def post(self, request: Request) -> Response:
        _mine(request).filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response({"unread": 0})

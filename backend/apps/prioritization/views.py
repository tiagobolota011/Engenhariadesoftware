from django.db import transaction
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsProductOwner
from apps.prioritization import services
from apps.prioritization.models import Assessment, Vote
from apps.requests.services import bump_version, get_request, lock_request, requests_for


class VoteView(APIView):
    """POST vota · DELETE retira o voto. Repetir não tem efeito (um voto por utilizador)."""

    def post(self, request: Request, pk: int) -> Response:
        item = get_request(request.user, pk)
        Vote.objects.get_or_create(request=item, user=request.user)
        return self._state(item, voted=True)

    def delete(self, request: Request, pk: int) -> Response:
        item = get_request(request.user, pk)
        Vote.objects.filter(request=item, user=request.user).delete()
        return self._state(item, voted=False)

    @staticmethod
    def _state(item, voted: bool) -> Response:
        return Response({"votes": item.votes.count(), "voted": voted})


def open_rows(request: Request) -> list[dict]:
    queryset = requests_for(request.user).filter(status__in=services.OPEN_STATUSES)
    if (category := request.query_params.get("category", "")).isdigit():
        queryset = queryset.filter(category_id=int(category))
    return [services.row(item) for item in queryset]


class PrioritizationView(APIView):
    permission_classes = [IsProductOwner]

    def get(self, request: Request) -> Response:
        return Response(services.ranked(open_rows(request)))


class ReorderView(APIView):
    """O PO move um pedido para uma posição, com motivo (fica no histórico)."""

    permission_classes = [IsProductOwner]

    @transaction.atomic
    def post(self, request: Request) -> Response:
        data = request.data
        errors: dict[str, list[str]] = {}
        position = data.get("position")
        if isinstance(position, bool) or not isinstance(position, int) or position < 0:
            errors["position"] = ["Send the new position as a whole number from 0."]
        reason = str(data.get("reason") or "").strip()
        if not reason:
            errors["reason"] = ["Say why this request is being moved."]
        if not isinstance(data.get("request"), int):
            errors["request"] = ["This field is required."]
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        item = lock_request(request.user, data["request"])
        assessment, _ = Assessment.objects.get_or_create(request=item)
        assessment.manual_rank = position
        assessment.override_reason = reason[:200]
        assessment.updated_by = request.user
        assessment.save()
        bump_version(item, request.user, f"Priority moved manually: {reason}")
        return Response({"id": item.id, "position": position})


class SuggestionView(APIView):
    """Ordem sugerida, calculada pelo sistema, com a explicação de cada posição."""

    permission_classes = [IsProductOwner]

    def get(self, request: Request) -> Response:
        rows = services.by_score(open_rows(request))
        return Response(
            {
                "basis": services.BASIS,
                "items": [
                    {
                        "id": r["id"],
                        "key": r["key"],
                        "title": r["title"],
                        "reason": services.explain(r),
                    }
                    for r in rows
                ],
            }
        )


class AcceptSuggestionView(APIView):
    """O PO aceita a sugestão: as posições manuais (da categoria filtrada) são retiradas."""

    permission_classes = [IsProductOwner]

    @transaction.atomic
    def post(self, request: Request) -> Response:
        for r in open_rows(request):
            if not r["manual"]:
                continue
            item = lock_request(request.user, r["id"])
            Assessment.objects.filter(request=item).update(manual_rank=None, override_reason="")
            bump_version(item, request.user, "Manual priority removed: suggestion accepted")
        return Response(status=status.HTTP_204_NO_CONTENT)

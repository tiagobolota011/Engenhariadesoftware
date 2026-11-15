from django.db import transaction
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api import payload, text
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


def open_rows(request: Request, filtered: bool = True) -> list[dict]:
    queryset = requests_for(request.user).filter(status__in=services.OPEN_STATUSES)
    category = request.query_params.get("category", "")
    if filtered and category.isdigit():
        queryset = queryset.filter(category_id=int(category))
    return [services.row(item) for item in queryset]


class PrioritizationView(APIView):
    permission_classes = [IsProductOwner]

    def get(self, request: Request) -> Response:
        # A ordem é sempre a global; o filtro de categoria só esconde linhas.
        rows = services.ranked(open_rows(request, filtered=False))
        category = request.query_params.get("category", "")
        if category.isdigit():
            rows = [r for r in rows if r["category_id"] == int(category)]
        return Response(rows)


class ReorderView(APIView):
    """O PO coloca um pedido imediatamente antes de outro (`before`), ou no fim (null).

    A posição é resolvida na ordem global, por isso mover dentro de uma categoria
    filtrada não faz o pedido saltar por cima dos das outras categorias.
    """

    permission_classes = [IsProductOwner]

    @transaction.atomic
    def post(self, request: Request) -> Response:
        data = payload(request)
        errors: dict[str, list[str]] = {}
        request_id, before = data.get("request"), data.get("before")
        if isinstance(request_id, bool) or not isinstance(request_id, int):
            errors["request"] = ["This field is required."]
        if before is not None and (isinstance(before, bool) or not isinstance(before, int)):
            errors["before"] = ["Send the id of the request to place this one before, or null."]
        reason = text(data.get("reason"))
        if not reason:
            errors["reason"] = ["Say why this request is being moved."]
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        item = lock_request(request.user, request_id)
        rows = services.ranked(open_rows(request, filtered=False))
        order = [r["id"] for r in rows]
        if item.id not in order:
            errors["request"] = ["Only open requests can be prioritised."]
        if before is not None and (before == item.id or before not in order):
            errors["before"] = ["Choose another open request from the table."]
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        order.remove(item.id)
        order.insert(order.index(before) if before is not None else len(order), item.id)
        Assessment.objects.get_or_create(request=item)
        # Todas as posições manuais são regravadas com o índice final, para que
        # cada movimento tenha efeito mesmo quando já havia outros pedidos fixados.
        pinned = {r["id"] for r in rows if r["manual"]} | {item.id}
        for position, pk in enumerate(order):
            if pk in pinned:
                Assessment.objects.filter(request_id=pk).update(manual_rank=position)
        Assessment.objects.filter(request=item).update(
            override_reason=reason[:200], updated_by=request.user
        )
        bump_version(item, request.user, f"Priority moved manually: {reason}")
        return Response({"id": item.id, "position": order.index(item.id)})


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

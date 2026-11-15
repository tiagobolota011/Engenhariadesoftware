"""Regras do módulo de pedidos partilhadas com os outros módulos."""

from django.db import transaction
from django.db.models import Count, Exists, Max, OuterRef, QuerySet
from django.shortcuts import get_object_or_404

from apps.collaboration.models import Workspace
from apps.prioritization.models import Vote
from apps.requests.models import FeatureRequest, RequestVersion, Tag


def workspace_id_of(user) -> int:
    return user.membership.workspace_id


def requests_for(user) -> QuerySet[FeatureRequest]:
    """Pedidos do workspace do utilizador, com contagem de votos e o seu voto."""
    return (
        FeatureRequest.objects.filter(workspace_id=workspace_id_of(user))
        .select_related("category", "author", "assessment")
        .prefetch_related("tags")
        .annotate(
            vote_count=Count("votes", distinct=True),
            voted=Exists(Vote.objects.filter(request=OuterRef("pk"), user=user)),
        )
    )


def get_request(user, pk) -> FeatureRequest:
    """Devolve o pedido ou 404 — nunca revela pedidos de outro workspace."""
    return get_object_or_404(requests_for(user), pk=pk)


def lock_request(user, pk) -> FeatureRequest:
    """Bloqueia a linha do pedido dentro de uma transação (escritas do PO)."""
    return get_object_or_404(
        FeatureRequest.objects.select_for_update().filter(workspace_id=workspace_id_of(user)),
        pk=pk,
    )


def normalise_tags(raw) -> list[str]:
    names = {str(t).strip().lstrip("#").strip().lower()[:30] for t in raw or []}
    return sorted(n for n in names if n)


@transaction.atomic
def create_request(*, author, title, description, category, tags, importance="") -> FeatureRequest:
    workspace = Workspace.objects.select_for_update().get(pk=workspace_id_of(author))
    last = FeatureRequest.objects.filter(workspace=workspace).aggregate(m=Max("number"))["m"]
    item = FeatureRequest.objects.create(
        workspace=workspace,
        number=(last or 0) + 1,
        title=title,
        description=description,
        importance=importance,
        category=category,
        author=author,
    )
    item.tags.set(
        Tag.objects.get_or_create(workspace=workspace, name=name)[0]
        for name in normalise_tags(tags)
    )
    RequestVersion.objects.create(request=item, number=1, actor=author, summary="Request created")
    return item


def bump_version(item: FeatureRequest, actor, summary: str) -> None:
    """Regista uma alteração: nova versão e linha de histórico."""
    item.version += 1
    item.save(update_fields=["version", "updated_at"])
    RequestVersion.objects.create(
        request=item, number=item.version, actor=actor, summary=summary[:300]
    )

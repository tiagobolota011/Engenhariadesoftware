"""Menções em comentários e notificações na aplicação (UC-08, UC-09)."""

import re

from django.contrib.auth.models import User

from apps.collaboration.models import Mention, Notification, NotificationKind
from apps.core.auth_views import display_name

# "@rui", "@ana.silva": o nome de utilizador termina numa letra ou dígito, para
# que a pontuação a seguir ("@rui," ou "@rui.") não faça parte dele. O "@" não
# pode vir colado a uma palavra (um endereço de email não é uma menção).
MENTION = re.compile(r"(?<![\w@])@([\w.+-]*\w)")


def mentioned_usernames(body: str) -> list[str]:
    """Nomes mencionados, em minúsculas, sem repetições e pela ordem do texto."""
    return list(dict.fromkeys(name.lower() for name in MENTION.findall(body)))


def record_mentions(comment) -> list[User]:
    """Guarda as menções de um comentário e devolve os utilizadores mencionados.

    Só contam membros do workspace do pedido, sem o próprio autor; nomes
    desconhecidos ou de outro workspace são ignorados, para não revelar quem
    existe noutras equipas.
    """
    names = mentioned_usernames(comment.body)
    if not names:
        return []
    users = [
        user
        for user in User.objects.filter(
            membership__workspace_id=comment.request.workspace_id, is_active=True
        )
        if user.username.lower() in names and user.pk != comment.author_id
    ]
    Mention.objects.bulk_create(
        [Mention(comment=comment, user=user) for user in users], ignore_conflicts=True
    )
    return users


def notify(recipients, *, actor, request, kind: str, message: str) -> int:
    """Cria uma notificação por destinatário; quem fez a ação nunca é notificado."""
    unique = {user.pk: user for user in recipients if user is not None and user.pk != actor.pk}
    Notification.objects.bulk_create(
        [
            Notification(recipient=user, actor=actor, request=request, kind=kind, message=message)
            for user in unique.values()
        ]
    )
    return len(unique)


def notify_mentions(comment) -> int:
    users = record_mentions(comment)
    item = comment.request
    return notify(
        users,
        actor=comment.author,
        request=item,
        kind=NotificationKind.MENTION,
        message=f"{display_name(comment.author)} mentioned you on {item.key} {item.title}"[:300],
    )


def notify_status_change(item, actor) -> int:
    return notify(
        [item.author],
        actor=actor,
        request=item,
        kind=NotificationKind.STATUS,
        message=f"{item.key} {item.title} is now {item.get_status_display()}"[:300],
    )


def notify_decision(item, actor) -> int:
    return notify(
        [item.author],
        actor=actor,
        request=item,
        kind=NotificationKind.DECISION,
        message=f"A decision was recorded on {item.key} {item.title}"[:300],
    )

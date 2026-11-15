from rest_framework.permissions import IsAuthenticated

from apps.collaboration.models import Role


def membership_of(user):
    return getattr(user, "membership", None)


class IsMember(IsAuthenticated):
    """Sessão iniciada e utilizador associado a um workspace."""

    def has_permission(self, request, view) -> bool:
        return super().has_permission(request, view) and membership_of(request.user) is not None


class IsProductOwner(IsMember):
    def has_permission(self, request, view) -> bool:
        return (
            super().has_permission(request, view)
            and request.user.membership.role == Role.PRODUCT_OWNER
        )

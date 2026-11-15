from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsMember, membership_of


def display_name(user) -> str:
    return user.get_full_name() or user.username


def profile(user) -> dict:
    membership = user.membership
    return {
        "id": user.id,
        "username": user.username,
        "name": display_name(user),
        "role": membership.role,
        "role_label": membership.get_role_display(),
        "workspace": {"id": membership.workspace_id, "name": membership.workspace.name},
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """GET /api/auth/csrf/ — entrega o cookie CSRF antes do primeiro POST."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response({"detail": "ok"})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        user = authenticate(
            request,
            username=str(request.data.get("username", "")),
            password=str(request.data.get("password", "")),
        )
        if user is None:
            return Response(
                {"detail": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST
            )
        if membership_of(user) is None:
            return Response(
                {"detail": "This account is not a member of any workspace."},
                status=status.HTTP_403_FORBIDDEN,
            )
        login(request, user)
        return Response(profile(user))


class LogoutView(APIView):
    def post(self, request: Request) -> Response:
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsMember]

    def get(self, request: Request) -> Response:
        return Response(profile(request.user))

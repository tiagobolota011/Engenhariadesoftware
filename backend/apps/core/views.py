from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.health import check_db


class HealthView(APIView):
    """GET /api/health/ — estado da API e da base de dados."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        if check_db():
            return Response({"status": "ok", "db": "up"})
        return Response(
            {"status": "degraded", "db": "down"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

"""Leitura defensiva do corpo dos pedidos à API."""

from collections.abc import Mapping

from rest_framework.exceptions import ValidationError


def payload(request) -> Mapping:
    """O corpo tem de ser um objeto JSON; outra coisa é um 400 e não um erro interno."""
    if not isinstance(request.data, Mapping):
        raise ValidationError({"detail": "Send a JSON object."})
    return request.data


def text(value) -> str:
    """Texto limpo: sem espaços nas pontas nem caracteres NUL (o PostgreSQL recusa-os)."""
    return str(value or "").replace("\x00", "").strip()

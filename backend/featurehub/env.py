"""Leitura de variáveis de ambiente obrigatórias."""

import os
from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured


def require_env(name: str, environ: Mapping[str, str] = os.environ) -> str:
    value = environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"{name} is required")
    return value

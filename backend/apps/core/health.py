"""Verificação de saúde da persistência."""

import logging

from django.db import DatabaseError, connection

logger = logging.getLogger("featurehub.health")


def check_db() -> bool:
    """Devolve True se a base de dados responde a ``SELECT 1``."""
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
    except DatabaseError:
        logger.warning("database check failed", exc_info=True)
        return False

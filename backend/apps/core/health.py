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
        # Descarta a ligação partida para que a próxima verificação volte a ligar
        # (o worker corre fora do ciclo de pedidos, onde o Django não o faz sozinho).
        try:
            connection.close()
        except DatabaseError:
            pass
        return False

"""Worker do FeatureHub (SCRUM-61): processo separado da API.

Nesta base apenas confirma a ligação à base de dados e regista um heartbeat.
A outbox, as notificações e os pedidos de IA serão acrescentados pelas
histórias respetivas.
"""

import logging
from collections.abc import Callable
from datetime import datetime

from django.utils import timezone

from apps.core.health import check_db

logger = logging.getLogger("featurehub.worker")


def run_once(now: Callable[[], datetime] = timezone.now) -> bool:
    db_up = check_db()
    logger.info("worker heartbeat db=%s at=%s", "up" if db_up else "down", now().isoformat())
    return db_up

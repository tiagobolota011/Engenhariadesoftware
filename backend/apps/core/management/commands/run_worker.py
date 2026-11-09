import logging
import os
import time

from django.core.management.base import BaseCommand

from apps.core.worker import run_once

logger = logging.getLogger("featurehub.worker")


class Command(BaseCommand):
    help = "Arranca o worker do FeatureHub (ciclo de heartbeat)."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Executa um único ciclo e termina.")
        parser.add_argument(
            "--interval",
            type=float,
            default=float(os.environ.get("WORKER_INTERVAL_SECONDS", "10")),
            help="Segundos entre ciclos (por omissão WORKER_INTERVAL_SECONDS ou 10).",
        )

    def handle(self, *args, once: bool, interval: float, **options):
        if once:
            run_once()
            return
        logger.info("worker started interval=%ss", interval)
        while True:
            try:
                run_once()
            except Exception:  # o worker não termina por causa de um ciclo falhado
                logger.exception("worker cycle failed")
            time.sleep(interval)

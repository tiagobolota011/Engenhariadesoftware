import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.collaboration.models import Membership, Role, Workspace
from apps.requests.models import Category

WORKSPACE = "FeatureHub Demo"
CATEGORIES = ["Account", "Catalog", "Interface", "Ordering", "Payments"]
PERSONAS = [
    ("mariana", "Mariana", "Costa", Role.CUSTOMER),
    ("pedro", "Pedro", "Nunes", Role.CUSTOMER),
    ("rui", "Rui", "Almeida", Role.PRODUCT_OWNER),
    ("catarina", "Catarina", "Reis", Role.DEVELOPER),
    ("duarte", "Duarte", "Fernandes", Role.PROJECT_MANAGER),
]


class Command(BaseCommand):
    help = "Cria o workspace de demonstração e as contas das personas (sem pedidos)."

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.environ.get("SEED_PASSWORD", "featurehub")
        workspace, _ = Workspace.objects.get_or_create(name=WORKSPACE)
        for username, first, last, role in PERSONAS:
            user, created = User.objects.get_or_create(
                username=username, defaults={"first_name": first, "last_name": last}
            )
            if created:
                user.set_password(password)
                user.save()
            Membership.objects.get_or_create(
                user=user, defaults={"workspace": workspace, "role": role}
            )
        self.seed_extra(workspace)
        self.stdout.write(
            self.style.SUCCESS(
                f"Workspace '{WORKSPACE}' pronto. Contas: "
                + ", ".join(p[0] for p in PERSONAS)
                + " (password de desenvolvimento definida por SEED_PASSWORD)."
            )
        )

    def seed_extra(self, workspace) -> None:
        """Dados de referência: as categorias dos wireframes. Não cria pedidos."""
        for name in CATEGORIES:
            Category.objects.get_or_create(workspace=workspace, name=name)

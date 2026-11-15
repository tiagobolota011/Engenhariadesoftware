from django.conf import settings
from django.db import models


class Workspace(models.Model):
    """Espaço de trabalho de uma equipa; todos os dados pertencem a um workspace."""

    name = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Role(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    PRODUCT_OWNER = "product_owner", "Product Owner"
    DEVELOPER = "developer", "Developer"
    PROJECT_MANAGER = "project_manager", "Project Manager"


class Membership(models.Model):
    """Liga um utilizador ao seu workspace e ao papel que nele desempenha."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membership"
    )
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices)

    def __str__(self) -> str:
        return f"{self.user} · {self.get_role_display()} · {self.workspace}"

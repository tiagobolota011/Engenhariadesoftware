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


class Comment(models.Model):
    """Comentário na discussão de um pedido; o PO pode marcar um como decisão."""

    request = models.ForeignKey(
        "feature_requests.FeatureRequest", on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="comments"
    )
    body = models.TextField()
    is_decision = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request"],
                condition=models.Q(is_decision=True),
                name="one_decision_per_request",
            )
        ]

    def __str__(self) -> str:
        return f"comment {self.pk} on {self.request_id}"


class Mention(models.Model):
    """Um membro do workspace mencionado (@username) num comentário."""

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="mentions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["comment", "user"], name="mention_unique_user")
        ]

    def __str__(self) -> str:
        return f"@{self.user} in comment {self.comment_id}"


class NotificationKind(models.TextChoices):
    MENTION = "mention", "Mention"
    STATUS = "status", "Status change"
    DECISION = "decision", "Decision"


class Notification(models.Model):
    """Aviso na aplicação para um utilizador, sempre ligado a um pedido."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    request = models.ForeignKey(
        "feature_requests.FeatureRequest", on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=20, choices=NotificationKind.choices)
    message = models.CharField(max_length=300)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["recipient", "read_at"])]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} for {self.recipient}: {self.message}"

from django.conf import settings
from django.db import models


class Category(models.Model):
    workspace = models.ForeignKey(
        "collaboration.Workspace", on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=60)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["workspace", "name"], name="category_unique_name")
        ]

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    workspace = models.ForeignKey(
        "collaboration.Workspace", on_delete=models.CASCADE, related_name="tags"
    )
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["workspace", "name"], name="tag_unique_name")
        ]

    def __str__(self) -> str:
        return self.name


class Status(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    PLANNED = "planned", "Planned"
    IN_PROGRESS = "in_progress", "In progress"
    RELEASED = "released", "Released"


# Só o Product Owner muda o estado, e só para um destes passos seguintes.
TRANSITIONS: dict[str, list[str]] = {
    Status.SUBMITTED: [Status.UNDER_REVIEW],
    Status.UNDER_REVIEW: [Status.APPROVED, Status.REJECTED],
    Status.APPROVED: [Status.PLANNED],
    Status.PLANNED: [Status.IN_PROGRESS],
    Status.IN_PROGRESS: [Status.RELEASED],
    Status.REJECTED: [],
    Status.RELEASED: [],
}


class FeatureRequest(models.Model):
    workspace = models.ForeignKey(
        "collaboration.Workspace", on_delete=models.CASCADE, related_name="requests"
    )
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    importance = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="requests")
    tags = models.ManyToManyField(Tag, blank=True, related_name="requests")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="feature_requests"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    # Versão para concorrência otimista: cada alteração do PO incrementa-a.
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["workspace", "number"], name="request_unique_number")
        ]
        indexes = [models.Index(fields=["workspace", "status"])]

    def __str__(self) -> str:
        return f"{self.key} {self.title}"

    @property
    def key(self) -> str:
        return f"REQ-{self.number:03d}"


class RequestVersion(models.Model):
    """Histórico de alterações de um pedido (auditoria com ator e data UTC)."""

    request = models.ForeignKey(FeatureRequest, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    summary = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-number"]
        constraints = [
            models.UniqueConstraint(fields=["request", "number"], name="version_unique_number")
        ]

    def __str__(self) -> str:
        return f"{self.request.key} v{self.number}"

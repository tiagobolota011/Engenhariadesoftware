from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Vote(models.Model):
    request = models.ForeignKey(
        "feature_requests.FeatureRequest", on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Regra de negócio: um voto por utilizador e pedido.
            models.UniqueConstraint(fields=["request", "user"], name="one_vote_per_user")
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.request_id}"


class Assessment(models.Model):
    """Avaliação do Product Owner: impacto, esforço e ordem manual."""

    request = models.OneToOneField(
        "feature_requests.FeatureRequest", on_delete=models.CASCADE, related_name="assessment"
    )
    impact = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    effort = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    manual_rank = models.PositiveIntegerField(null=True, blank=True)
    override_reason = models.CharField(max_length=200, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"assessment of {self.request_id}"

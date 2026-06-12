from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models import TimeStampedModel


class Deal(TimeStampedModel):
    class Stage(models.TextChoices):
        PROSPECT = "prospect", "Prospect"
        QUALIFIED = "qualified", "Qualified"
        PROPOSAL = "proposal", "Proposal"
        NEGOTIATION = "negotiation", "Negotiation"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    name = models.CharField(max_length=200)
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="deals"
    )
    value = models.DecimalField(max_digits=14, decimal_places=2)
    stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.PROSPECT, db_index=True
    )
    description = models.TextField(blank=True)
    expected_close_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
    )

    class Meta:
        db_table = "deals"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["stage", "-created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(value__gte=0), name="deal_value_non_negative"
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("deals:detail", args=[self.pk])

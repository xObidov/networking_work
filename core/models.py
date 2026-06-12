"""Abstract base models shared by every app."""
from django.db import models


class TimeStampedModel(models.Model):
    """Gives every table the audit fields `created_at` / `updated_at`."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

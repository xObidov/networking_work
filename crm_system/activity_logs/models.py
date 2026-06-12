from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class ActivityLog(TimeStampedModel):
    """Append-only audit trail of every significant action in the system."""

    class Action(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        ASSIGN = "assign", "Assign"
        CONVERT = "convert", "Convert"
        STATUS_CHANGE = "status_change", "Status Change"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    description = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "activity_logs"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.user} {self.action}: {self.description}"

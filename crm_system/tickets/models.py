from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from core.models import TimeStampedModel


class Ticket(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="tickets"
    )
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tickets",
    )

    class Meta:
        db_table = "tickets"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "priority"])]

    def __str__(self):
        return f"{self.ticket_number} — {self.subject}"

    def get_absolute_url(self):
        return reverse("tickets:detail", args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        """TKT-YYYY-0001 style, race-safe via select_for_update on last row."""
        year = timezone.now().year
        prefix = f"TKT-{year}-"
        with transaction.atomic():
            last = (
                Ticket.objects.select_for_update()
                .filter(ticket_number__startswith=prefix)
                .order_by("-ticket_number")
                .first()
            )
            seq = int(last.ticket_number.rsplit("-", 1)[1]) + 1 if last else 1
        return f"{prefix}{seq:04d}"


class TicketReply(TimeStampedModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    body = models.TextField()

    class Meta:
        db_table = "ticket_replies"
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply on {self.ticket} by {self.author}"

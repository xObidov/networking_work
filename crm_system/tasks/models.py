from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.models import TimeStampedModel
from core.validators import FILE_VALIDATORS


class Task(TimeStampedModel):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["assigned_to", "status"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("tasks:detail", args=[self.pk])

    @property
    def is_overdue(self):
        return (
            self.due_date is not None
            and self.status in (self.Status.PENDING, self.Status.IN_PROGRESS)
            and self.due_date < timezone.localdate()
        )


class TaskComment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    body = models.TextField()

    class Meta:
        db_table = "task_comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.task} by {self.author}"


class TaskAttachment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="task_attachments/%Y/%m/", validators=FILE_VALIDATORS)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        db_table = "task_attachments"
        ordering = ["-created_at"]

    def __str__(self):
        return self.file.name

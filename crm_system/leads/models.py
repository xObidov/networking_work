from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models import TimeStampedModel


class Lead(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        PROPOSAL_SENT = "proposal_sent", "Proposal Sent"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        REFERRAL = "referral", "Referral"
        SOCIAL_MEDIA = "social_media", "Social Media"
        COLD_CALL = "cold_call", "Cold Call"
        EMAIL_CAMPAIGN = "email_campaign", "Email Campaign"
        EVENT = "event", "Event"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=150, blank=True)
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.WEBSITE
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, db_index=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    notes = models.TextField(blank=True)
    converted_customer = models.OneToOneField(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_lead",
    )

    class Meta:
        db_table = "leads"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("leads:detail", args=[self.pk])

    @property
    def is_converted(self):
        return self.converted_customer_id is not None


class LeadNote(TimeStampedModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="lead_notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    body = models.TextField()

    class Meta:
        db_table = "lead_notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.lead} by {self.author}"

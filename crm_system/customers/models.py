from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from core.models import TimeStampedModel
from core.validators import FILE_VALIDATORS


class Tag(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#0d6efd")

    class Meta:
        db_table = "customer_tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        PROSPECT = "prospect", _("Prospect")

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=150, blank=True, db_index=True)
    position = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROSPECT, db_index=True
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="customers")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
    )

    class Meta:
        db_table = "customers"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["last_name", "first_name"])]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("customers:detail", args=[self.pk])


class CustomerDocument(TimeStampedModel):
    """Uploaded files attached to a customer (contracts, documents, ...)."""

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="documents"
    )
    file = models.FileField(
        upload_to="customer_documents/%Y/%m/", validators=FILE_VALIDATORS
    )
    name = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        db_table = "customer_documents"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

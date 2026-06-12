from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from core.models import TimeStampedModel


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"

    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.PROTECT, related_name="invoices"
    )
    deal = models.ForeignKey(
        "deals.Deal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("12.00"),
        help_text="Tax percentage, e.g. 12.00",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    due_date = models.DateField(null=True, blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        db_table = "invoices"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0), name="invoice_amount_non_negative"
            ),
        ]

    def __str__(self):
        return self.invoice_number

    def get_absolute_url(self):
        return reverse("invoices:detail", args=[self.pk])

    @property
    def tax_amount(self) -> Decimal:
        return (self.amount * self.tax_rate / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def total_amount(self) -> Decimal:
        return self.amount + self.tax_amount

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        prefix = f"INV-{year}-"
        with transaction.atomic():
            last = (
                Invoice.objects.select_for_update()
                .filter(invoice_number__startswith=prefix)
                .order_by("-invoice_number")
                .first()
            )
            seq = int(last.invoice_number.rsplit("-", 1)[1]) + 1 if last else 1
        return f"{prefix}{seq:04d}"

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.roles import Role
from core.testing import make_customer, make_user

from .models import Invoice


class InvoiceModelTests(TestCase):
    def setUp(self):
        self.customer = make_customer()

    def test_totals_computed_from_tax_rate(self):
        invoice = Invoice.objects.create(
            customer=self.customer, amount=Decimal("100.00"),
            tax_rate=Decimal("12.00"),
        )
        self.assertEqual(invoice.tax_amount, Decimal("12.00"))
        self.assertEqual(invoice.total_amount, Decimal("112.00"))

    def test_sequential_invoice_numbers(self):
        i1 = Invoice.objects.create(customer=self.customer, amount=1)
        i2 = Invoice.objects.create(customer=self.customer, amount=2)
        year = timezone.now().year
        self.assertEqual(i1.invoice_number, f"INV-{year}-0001")
        self.assertEqual(i2.invoice_number, f"INV-{year}-0002")


class InvoiceViewTests(TestCase):
    def setUp(self):
        self.manager = make_user(email="inv-mgr@test.local", role=Role.MANAGER)
        self.customer = make_customer()
        self.client.force_login(self.manager)

    def test_create_invoice(self):
        response = self.client.post(reverse("invoices:add"), {
            "customer": self.customer.pk, "amount": "250.00",
            "tax_rate": "12.00", "status": "pending",
        })
        invoice = Invoice.objects.get()
        self.assertRedirects(response, invoice.get_absolute_url())
        self.assertEqual(invoice.issued_by, self.manager)

    def test_pdf_download(self):
        invoice = Invoice.objects.create(customer=self.customer, amount=Decimal("99.00"))
        response = self.client.get(reverse("invoices:pdf", args=[invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(invoice.invoice_number, response["Content-Disposition"])

    def test_sales_agent_cannot_view_invoices(self):
        sales = make_user(email="inv-sales@test.local", role=Role.SALES_AGENT)
        self.client.force_login(sales)
        response = self.client.get(reverse("invoices:list"))
        self.assertEqual(response.status_code, 403)


class InvoiceAPITests(TestCase):
    def setUp(self):
        self.client.force_login(make_user(email="inv-api@test.local", role=Role.ADMIN))
        self.customer = make_customer()

    def test_create_returns_computed_totals(self):
        response = self.client.post("/api/v1/invoices/", {
            "customer": self.customer.pk, "amount": "200.00",
            "tax_rate": "10.00", "status": "draft",
        })
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()
        self.assertEqual(data["tax_amount"], "20.00")
        self.assertEqual(data["total_amount"], "220.00")

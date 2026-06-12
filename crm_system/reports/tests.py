from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.roles import Role
from core.testing import make_customer, make_user
from deals.models import Deal


class ReportTests(TestCase):
    def setUp(self):
        self.manager = make_user(email="rep-mgr@test.local", role=Role.MANAGER)
        self.client.force_login(self.manager)
        customer = make_customer()
        Deal.objects.create(
            customer=customer, name="Won deal", value=Decimal("500.00"),
            stage=Deal.Stage.WON, owner=self.manager,
        )

    def test_index_lists_all_reports(self):
        response = self.client.get(reverse("reports:index"))
        for title in ["Customer Report", "Lead Report", "Deal Report",
                      "Revenue Report", "Task Report", "Employee Performance Report"]:
            self.assertContains(response, title)

    def test_detail_renders_rows(self):
        response = self.client.get(reverse("reports:detail", args=["deals"]))
        self.assertContains(response, "Won deal")

    def test_unknown_report_404(self):
        self.assertEqual(
            self.client.get(reverse("reports:detail", args=["nope"])).status_code, 404
        )

    def test_excel_export(self):
        response = self.client.get(reverse("reports:export", args=["employees", "xlsx"]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])

    def test_pdf_export(self):
        response = self.client.get(reverse("reports:export", args=["deals", "pdf"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_sales_agent_blocked(self):
        agent = make_user(email="rep-agent@test.local", role=Role.SALES_AGENT)
        self.client.force_login(agent)
        self.assertEqual(self.client.get(reverse("reports:index")).status_code, 403)

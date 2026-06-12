from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.testing import make_customer, make_user
from deals.models import Deal
from leads.models import Lead


class DashboardTests(TestCase):
    def setUp(self):
        self.user = make_user(email="dash@test.local")
        self.client.force_login(self.user)
        customer = make_customer()
        Deal.objects.create(
            customer=customer, name="Won", value=Decimal("1000.00"),
            stage=Deal.Stage.WON, owner=self.user,
        )
        Lead.objects.create(name="Lead A", status=Lead.Status.WON)
        Lead.objects.create(name="Lead B", status=Lead.Status.NEW)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)

    def test_kpis(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.context["total_customers"], 1)
        self.assertEqual(response.context["total_leads"], 2)
        self.assertEqual(response.context["total_revenue"], Decimal("1000.00"))

    def test_revenue_chart(self):
        data = self.client.get(reverse("dashboard:chart_revenue")).json()
        self.assertEqual(len(data["labels"]), 12)
        self.assertEqual(sum(data["data"]), 1000.0)

    def test_lead_conversion_chart(self):
        data = self.client.get(reverse("dashboard:chart_leads")).json()
        self.assertEqual(data["conversion_rate"], 50.0)

    def test_growth_chart(self):
        data = self.client.get(reverse("dashboard:chart_growth")).json()
        self.assertEqual(sum(data["data"]), 1)

    def test_performance_chart(self):
        data = self.client.get(reverse("dashboard:chart_performance")).json()
        self.assertEqual(data["data"], [1000.0])

    def test_charts_require_auth(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:chart_revenue"))
        self.assertEqual(response.status_code, 403)

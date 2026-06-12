import json

from django.test import TestCase
from django.urls import reverse

from core.roles import Role
from core.testing import make_customer, make_user

from .models import Deal


class DealViewTests(TestCase):
    def setUp(self):
        self.agent = make_user(email="deal-agent@test.local", role=Role.SALES_AGENT)
        self.customer = make_customer()
        self.client.force_login(self.agent)

    def _make_deal(self, **kwargs):
        defaults = {"name": "Big Deal", "customer": self.customer, "value": "5000.00"}
        defaults.update(kwargs)
        return Deal.objects.create(**defaults)

    def test_kanban_shows_columns_and_deals(self):
        self._make_deal()
        response = self.client.get(reverse("deals:kanban"))
        self.assertContains(response, "Big Deal")
        for _, label in Deal.Stage.choices:
            self.assertContains(response, label)

    def test_create_deal(self):
        response = self.client.post(reverse("deals:add"), {
            "name": "New Deal", "customer": self.customer.pk,
            "value": "1234.50", "stage": "prospect",
        })
        deal = Deal.objects.get(name="New Deal")
        self.assertRedirects(response, deal.get_absolute_url())

    def test_ajax_stage_update(self):
        deal = self._make_deal()
        response = self.client.post(
            reverse("deals:update_stage", args=[deal.pk]),
            json.dumps({"stage": "won"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        deal.refresh_from_db()
        self.assertEqual(deal.stage, Deal.Stage.WON)

    def test_ajax_stage_update_rejects_invalid_stage(self):
        deal = self._make_deal()
        response = self.client.post(
            reverse("deals:update_stage", args=[deal.pk]),
            json.dumps({"stage": "nonsense"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_stage_update_forbidden_for_support(self):
        deal = self._make_deal()
        self.client.force_login(make_user(email="sup3@test.local", role=Role.SUPPORT_AGENT))
        response = self.client.post(
            reverse("deals:update_stage", args=[deal.pk]),
            json.dumps({"stage": "won"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_kanban_won_total(self):
        self._make_deal(stage=Deal.Stage.WON, value="100.00")
        self._make_deal(name="Other", stage=Deal.Stage.WON, value="50.00")
        response = self.client.get(reverse("deals:kanban"))
        self.assertEqual(response.context["won_total"], 150)


class DealAPITests(TestCase):
    def setUp(self):
        self.client.force_login(make_user(email="deal-api@test.local", role=Role.MANAGER))
        self.customer = make_customer()

    def test_create_and_filter_by_stage(self):
        create = self.client.post("/api/v1/deals/", {
            "name": "API Deal", "customer": self.customer.pk,
            "value": "999.99", "stage": "qualified",
        })
        self.assertEqual(create.status_code, 201, create.content)
        listing = self.client.get("/api/v1/deals/", {"stage": "qualified"})
        self.assertEqual(listing.json()["count"], 1)

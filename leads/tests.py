from django.test import TestCase
from django.urls import reverse

from core.roles import Role
from core.testing import make_user
from customers.models import Customer

from .models import Lead


class LeadViewTests(TestCase):
    def setUp(self):
        self.agent = make_user(email="lead-agent@test.local", role=Role.SALES_AGENT)
        self.other = make_user(email="other@test.local", role=Role.SALES_AGENT)
        self.client.force_login(self.agent)

    def _make_lead(self, **kwargs):
        defaults = {"name": "Big Corp Lead", "email": "lead@corp.test", "company": "Big Corp"}
        defaults.update(kwargs)
        return Lead.objects.create(**defaults)

    def test_list_and_filter(self):
        self._make_lead(status=Lead.Status.NEW)
        self._make_lead(name="Won Lead", status=Lead.Status.WON, email="w@x.test")
        response = self.client.get(reverse("leads:list"), {"status": "new"})
        self.assertContains(response, "Big Corp Lead")
        self.assertNotContains(response, "Won Lead")

    def test_create_lead_notifies_assignee(self):
        self.client.post(reverse("leads:add"), {
            "name": "Assigned Lead", "source": "website", "status": "new",
            "assigned_to": self.other.pk,
        })
        self.assertTrue(Lead.objects.filter(name="Assigned Lead").exists())
        self.assertTrue(
            self.other.notifications.filter(title__icontains="lead").exists()
        )

    def test_add_note(self):
        lead = self._make_lead()
        self.client.post(reverse("leads:add_note", args=[lead.pk]), {"body": "Called them."})
        self.assertEqual(lead.lead_notes.count(), 1)

    def test_convert_creates_customer_and_marks_won(self):
        lead = self._make_lead(name="John Doe", email="john@corp.test")
        response = self.client.post(reverse("leads:convert", args=[lead.pk]))
        lead.refresh_from_db()
        self.assertEqual(lead.status, Lead.Status.WON)
        self.assertIsNotNone(lead.converted_customer)
        customer = lead.converted_customer
        self.assertEqual(customer.first_name, "John")
        self.assertEqual(customer.last_name, "Doe")
        self.assertRedirects(response, reverse("customers:detail", args=[customer.pk]))

    def test_convert_twice_is_idempotent(self):
        lead = self._make_lead(email="once@x.test")
        self.client.post(reverse("leads:convert", args=[lead.pk]))
        self.client.post(reverse("leads:convert", args=[lead.pk]))
        self.assertEqual(Customer.objects.filter(email="once@x.test").count(), 1)

    def test_support_agent_cannot_access_leads(self):
        support = make_user(email="sup2@test.local", role=Role.SUPPORT_AGENT)
        self.client.force_login(support)
        response = self.client.get(reverse("leads:list"))
        self.assertEqual(response.status_code, 403)


class LeadAPITests(TestCase):
    def setUp(self):
        self.client.force_login(make_user(email="lead-api@test.local", role=Role.MANAGER))

    def test_create_and_note(self):
        create = self.client.post("/api/v1/leads/", {
            "name": "API Lead", "source": "referral", "status": "new",
        })
        self.assertEqual(create.status_code, 201, create.content)
        pk = create.json()["id"]
        note = self.client.post(f"/api/v1/leads/{pk}/add_note/", {"body": "via API"})
        self.assertEqual(note.status_code, 201)
        detail = self.client.get(f"/api/v1/leads/{pk}/")
        self.assertEqual(len(detail.json()["lead_notes"]), 1)

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.roles import Role
from core.testing import make_customer, make_user

from .models import Ticket


class TicketModelTests(TestCase):
    def test_sequential_ticket_numbers(self):
        customer = make_customer()
        t1 = Ticket.objects.create(customer=customer, subject="A", description="x")
        t2 = Ticket.objects.create(customer=customer, subject="B", description="y")
        year = timezone.now().year
        self.assertEqual(t1.ticket_number, f"TKT-{year}-0001")
        self.assertEqual(t2.ticket_number, f"TKT-{year}-0002")


class TicketViewTests(TestCase):
    def setUp(self):
        self.support = make_user(email="ticket-sup@test.local", role=Role.SUPPORT_AGENT)
        self.customer = make_customer()
        self.client.force_login(self.support)

    def test_create_ticket(self):
        response = self.client.post(reverse("tickets:add"), {
            "customer": self.customer.pk, "subject": "Broken thing",
            "description": "It broke", "priority": "high", "status": "open",
        })
        ticket = Ticket.objects.get(subject="Broken thing")
        self.assertRedirects(response, ticket.get_absolute_url())
        self.assertEqual(ticket.created_by, self.support)

    def test_reply_notifies_assignee(self):
        other = make_user(email="other-sup@test.local", role=Role.SUPPORT_AGENT)
        ticket = Ticket.objects.create(
            customer=self.customer, subject="S", description="d", assigned_to=other
        )
        self.client.post(reverse("tickets:reply", args=[ticket.pk]), {"body": "On it"})
        self.assertEqual(ticket.replies.count(), 1)
        self.assertTrue(other.notifications.filter(title__icontains="reply").exists())

    def test_status_change_notifies_assignee(self):
        ticket = Ticket.objects.create(
            customer=self.customer, subject="S2", description="d",
            assigned_to=self.support,
        )
        self.client.post(reverse("tickets:edit", args=[ticket.pk]), {
            "customer": self.customer.pk, "subject": "S2", "description": "d",
            "priority": "medium", "status": "resolved", "assigned_to": self.support.pk,
        })
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.RESOLVED)

    def test_sales_agent_cannot_view_tickets(self):
        sales = make_user(email="sales-x@test.local", role=Role.SALES_AGENT)
        self.client.force_login(sales)
        response = self.client.get(reverse("tickets:list"))
        self.assertEqual(response.status_code, 403)


class TicketAPITests(TestCase):
    def setUp(self):
        self.client.force_login(make_user(email="tic-api@test.local", role=Role.ADMIN))
        self.customer = make_customer()

    def test_create_and_reply(self):
        create = self.client.post("/api/v1/tickets/", {
            "customer": self.customer.pk, "subject": "API ticket",
            "description": "via api", "priority": "low", "status": "open",
        })
        self.assertEqual(create.status_code, 201, create.content)
        pk = create.json()["id"]
        self.assertTrue(create.json()["ticket_number"].startswith("TKT-"))
        reply = self.client.post(f"/api/v1/tickets/{pk}/reply/", {"body": "ack"})
        self.assertEqual(reply.status_code, 201)


class ContactFormAPITests(TestCase):
    """Public contact-form endpoint: website submissions become tickets."""

    URL = "/api/v1/contact/"

    def test_anonymous_submission_creates_customer_and_ticket(self):
        response = self.client.post(self.URL, {
            "name": "Said Kamol",
            "email": "visitor@example.com",
            "message": "Mahsulotlaringiz haqida ma'lumot kerak.",
        })
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(response.json()["ticket_number"].startswith("TKT-"))
        from customers.models import Customer
        customer = Customer.objects.get(email="visitor@example.com")
        self.assertEqual(customer.first_name, "Said")
        ticket = Ticket.objects.get(customer=customer)
        self.assertIn("Aloqa formasi", ticket.subject)
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

    def test_existing_customer_is_reused(self):
        existing = make_customer(email="repeat@example.com")
        self.client.post(self.URL, {
            "name": "Repeat Visitor", "email": "repeat@example.com",
            "message": "Yana bir savol.",
        })
        from customers.models import Customer
        self.assertEqual(Customer.objects.filter(email="repeat@example.com").count(), 1)
        self.assertEqual(existing.tickets.count(), 1)

    def test_admins_get_notified(self):
        admin = make_user(email="contact-admin@test.local", role=Role.ADMIN)
        sales = make_user(email="contact-sales@test.local", role=Role.SALES_AGENT)
        self.client.post(self.URL, {
            "name": "N", "email": "n@example.com", "message": "msg",
        })
        self.assertTrue(admin.notifications.filter(title__icontains="murojaat").exists())
        self.assertFalse(sales.notifications.exists())

    def test_invalid_email_rejected(self):
        response = self.client.post(self.URL, {
            "name": "X", "email": "not-an-email", "message": "msg",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_shared_key_enforced_when_configured(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"CONTACT_API_KEY": "sekret"}):
            bad = self.client.post(self.URL, {
                "name": "X", "email": "x@example.com", "message": "m",
            })
            self.assertEqual(bad.status_code, 403)
            good = self.client.post(self.URL, {
                "name": "X", "email": "x@example.com", "message": "m",
            }, headers={"X-Contact-Key": "sekret"})
            self.assertEqual(good.status_code, 201)

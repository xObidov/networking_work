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

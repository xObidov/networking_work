from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from core.roles import Role
from core.testing import make_customer, make_user

from .models import Customer, Tag


class CustomerModelTests(TestCase):
    def test_full_name_and_str(self):
        customer = make_customer(first_name="John", last_name="Smith")
        self.assertEqual(customer.full_name, "John Smith")
        self.assertEqual(str(customer), "John Smith")


class CustomerViewTests(TestCase):
    def setUp(self):
        self.agent = make_user(email="agent@test.local", role=Role.SALES_AGENT)
        self.support = make_user(email="sup@test.local", role=Role.SUPPORT_AGENT)
        self.client.force_login(self.agent)

    def test_list_view(self):
        make_customer()
        response = self.client.get(reverse("customers:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acme")

    def test_search_filter(self):
        make_customer(first_name="Findable", email="findme@x.test")
        make_customer(first_name="Hidden", email="hide@x.test")
        response = self.client.get(reverse("customers:list"), {"q": "Findable"})
        self.assertContains(response, "Findable")
        self.assertNotContains(response, "Hidden")

    def test_status_filter(self):
        make_customer(status=Customer.Status.ACTIVE, email="a1@x.test")
        make_customer(status=Customer.Status.INACTIVE, email="a2@x.test", first_name="Zzhidden")
        response = self.client.get(reverse("customers:list"), {"status": "active"})
        self.assertNotContains(response, "Zzhidden")

    def test_create_customer_logs_activity(self):
        response = self.client.post(reverse("customers:add"), {
            "first_name": "New", "last_name": "Client",
            "email": "client@new.test", "status": "prospect",
        })
        customer = Customer.objects.get(email="client@new.test")
        self.assertRedirects(response, customer.get_absolute_url())
        self.assertTrue(
            self.agent.activity_logs.filter(action="create").exists()
        )

    def test_update_customer(self):
        customer = make_customer()
        response = self.client.post(
            reverse("customers:edit", args=[customer.pk]),
            {"first_name": "Edited", "last_name": customer.last_name,
             "email": customer.email, "status": "active"},
        )
        customer.refresh_from_db()
        self.assertEqual(customer.first_name, "Edited")
        self.assertEqual(customer.status, "active")

    def test_delete_customer(self):
        customer = make_customer()
        self.client.post(reverse("customers:delete", args=[customer.pk]))
        self.assertFalse(Customer.objects.filter(pk=customer.pk).exists())

    def test_detail_view_shows_timeline_sections(self):
        customer = make_customer()
        response = self.client.get(customer.get_absolute_url())
        self.assertContains(response, "Activity Timeline")
        self.assertContains(response, "Documents")

    def test_support_agent_cannot_modify(self):
        self.client.force_login(self.support)
        response = self.client.get(reverse("customers:add"))
        self.assertEqual(response.status_code, 403)

    def test_support_agent_can_view(self):
        self.client.force_login(self.support)
        response = self.client.get(reverse("customers:list"))
        self.assertEqual(response.status_code, 200)

    def test_document_upload_rejects_bad_extension(self):
        customer = make_customer()
        bad = SimpleUploadedFile("evil.exe", b"MZ...", content_type="application/x-msdownload")
        self.client.post(
            reverse("customers:upload_document", args=[customer.pk]),
            {"name": "Evil", "file": bad},
        )
        self.assertEqual(customer.documents.count(), 0)

    def test_document_upload_accepts_pdf(self):
        customer = make_customer()
        good = SimpleUploadedFile("contract.pdf", b"%PDF-1.4", content_type="application/pdf")
        self.client.post(
            reverse("customers:upload_document", args=[customer.pk]),
            {"name": "Contract", "file": good},
        )
        self.assertEqual(customer.documents.count(), 1)


class CustomerAPITests(TestCase):
    def setUp(self):
        self.agent = make_user(email="api@test.local", role=Role.MANAGER)
        self.client.force_login(self.agent)

    def test_crud_via_api(self):
        tag = Tag.objects.create(name="VIP")
        create = self.client.post("/api/v1/customers/", {
            "first_name": "Api", "last_name": "Client",
            "email": "api-client@x.test", "status": "active",
            "tag_ids": [tag.pk],
        })
        self.assertEqual(create.status_code, 201, create.content)
        pk = create.json()["id"]

        detail = self.client.get(f"/api/v1/customers/{pk}/")
        self.assertEqual(detail.json()["tags"][0]["name"], "VIP")

        patch = self.client.patch(
            f"/api/v1/customers/{pk}/",
            {"city": "Tashkent"},
            content_type="application/json",
        )
        self.assertEqual(patch.json()["city"], "Tashkent")

        delete = self.client.delete(f"/api/v1/customers/{pk}/")
        self.assertEqual(delete.status_code, 204)

    def test_api_search(self):
        make_customer(first_name="Searchable", email="s@x.test")
        response = self.client.get("/api/v1/customers/", {"search": "Searchable"})
        self.assertEqual(response.json()["count"], 1)

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from core.roles import Role, has_module_permission
from core.testing import PASSWORD, make_user

from .models import User
from .tokens import make_verification_token, read_verification_token


class UserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(email="a@b.test", password="x-Pass-123")
        self.assertEqual(user.email, "a@b.test")
        self.assertTrue(user.check_password("x-Pass-123"))
        self.assertFalse(user.is_staff)

    def test_create_superuser_gets_super_admin_role(self):
        user = User.objects.create_superuser(email="root@b.test", password="x-Pass-123")
        self.assertEqual(user.role, Role.SUPER_ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_email_verified)

    def test_email_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="x")

    def test_initials(self):
        user = make_user(first_name="Jane", last_name="Doe")
        self.assertEqual(user.initials, "JD")


class RBACTests(TestCase):
    def test_super_admin_can_do_everything(self):
        user = make_user(role=Role.SUPER_ADMIN)
        self.assertTrue(has_module_permission(user, "invoices", "modify"))
        self.assertTrue(has_module_permission(user, "activity_logs", "view"))

    def test_sales_agent_cannot_view_invoices(self):
        user = make_user(role=Role.SALES_AGENT)
        self.assertFalse(has_module_permission(user, "invoices", "view"))
        self.assertTrue(has_module_permission(user, "leads", "modify"))

    def test_support_agent_cannot_modify_leads(self):
        user = make_user(role=Role.SUPPORT_AGENT)
        self.assertFalse(has_module_permission(user, "leads", "modify"))
        self.assertTrue(has_module_permission(user, "tickets", "modify"))


class AuthViewTests(TestCase):
    def setUp(self):
        self.user = make_user(email="login@test.local")

    def test_login_page_renders(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login@test.local", "password": PASSWORD},
        )
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_login_without_remember_me_expires_at_browser_close(self):
        self.client.post(
            reverse("accounts:login"),
            {"username": "login@test.local", "password": PASSWORD},
        )
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_with_remember_me_keeps_session(self):
        self.client.post(
            reverse("accounts:login"),
            {"username": "login@test.local", "password": PASSWORD, "remember_me": "on"},
        )
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_registration_creates_user_and_sends_verification(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "New",
            "last_name": "Person",
            "email": "new@test.local",
            "password1": "Sup3r-secret-pass",
            "password2": "Sup3r-secret-pass",
        })
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(User.objects.filter(email="new@test.local").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].body.lower())

    def test_email_verification_flow(self):
        token = make_verification_token(self.user)
        self.assertEqual(read_verification_token(token), self.user.pk)
        response = self.client.get(reverse("accounts:verify_email", args=[token]))
        self.assertRedirects(response, reverse("accounts:login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_invalid_verification_token_rejected(self):
        self.assertIsNone(read_verification_token("garbage"))

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_update(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:profile"), {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+998901234567",
            "position": "Engineer",
        })
        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")


class JWTAuthTests(TestCase):
    def setUp(self):
        self.user = make_user(email="jwt@test.local")

    def test_obtain_and_refresh_token(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "jwt@test.local", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        tokens = response.json()
        self.assertIn("access", tokens)

        refresh = self.client.post(
            reverse("token_refresh"), {"refresh": tokens["refresh"]}
        )
        self.assertEqual(refresh.status_code, 200)

    def test_wrong_password_rejected(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "jwt@test.local", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 401)

    def test_api_requires_authentication(self):
        response = self.client.get("/api/v1/customers/")
        self.assertEqual(response.status_code, 401)

    def test_api_with_bearer_token(self):
        tokens = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "jwt@test.local", "password": PASSWORD},
        ).json()
        response = self.client.get(
            "/api/v1/customers/",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(response.status_code, 200)

from django.test import TestCase
from django.urls import reverse

from core.roles import Role
from core.testing import PASSWORD, make_user

from .models import ActivityLog
from .services import log_activity


class ActivityLogTests(TestCase):
    def test_login_creates_log_entry(self):
        user = make_user(email="log-login@test.local")
        self.client.post(
            reverse("accounts:login"),
            {"username": user.email, "password": PASSWORD},
        )
        self.assertTrue(
            ActivityLog.objects.filter(user=user, action="login").exists()
        )

    def test_log_activity_truncates_description(self):
        user = make_user(email="trunc@test.local")
        log_activity(user, "update", "x" * 1000)
        self.assertEqual(len(ActivityLog.objects.get().description), 500)

    def test_view_restricted_to_admins(self):
        agent = make_user(email="log-agent@test.local", role=Role.SALES_AGENT)
        self.client.force_login(agent)
        self.assertEqual(self.client.get(reverse("activity_logs:list")).status_code, 403)

        admin = make_user(email="log-admin@test.local", role=Role.ADMIN)
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("activity_logs:list")).status_code, 200)

    def test_api_read_only(self):
        admin = make_user(email="log-api@test.local", role=Role.ADMIN)
        self.client.force_login(admin)
        log_activity(admin, "create", "something")
        listing = self.client.get("/api/v1/activity-logs/")
        self.assertEqual(listing.status_code, 200)
        post = self.client.post("/api/v1/activity-logs/", {"action": "create"})
        # Writes are blocked: RBAC denies "modify" on the audit log (403)
        # before the read-only ViewSet would return 405.
        self.assertEqual(post.status_code, 403)

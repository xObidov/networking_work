from django.test import TestCase
from django.urls import reverse

from core.testing import make_user

from .models import Notification
from .services import notify


class NotificationTests(TestCase):
    def setUp(self):
        self.user = make_user(email="notif@test.local")
        self.client.force_login(self.user)

    def test_notify_service_creates_row(self):
        notify(self.user, "Hello", "World", "/some/link/")
        self.assertEqual(self.user.notifications.count(), 1)

    def test_notify_none_user_is_noop(self):
        self.assertIsNone(notify(None, "x"))

    def test_unread_count_in_context(self):
        notify(self.user, "Unread one")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.context["unread_count"], 1)

    def test_mark_read(self):
        n = notify(self.user, "Read me")
        self.client.post(
            reverse("notifications:mark_read", args=[n.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_cannot_mark_other_users_notification(self):
        other = make_user(email="other-notif@test.local")
        n = notify(other, "Not yours")
        response = self.client.post(reverse("notifications:mark_read", args=[n.pk]))
        self.assertEqual(response.status_code, 404)

    def test_mark_all_read(self):
        notify(self.user, "a")
        notify(self.user, "b")
        self.client.post(
            reverse("notifications:mark_all_read"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(self.user.notifications.filter(is_read=False).count(), 0)

    def test_api_scoped_to_current_user(self):
        other = make_user(email="other2@test.local")
        notify(other, "theirs")
        notify(self.user, "mine")
        response = self.client.get("/api/v1/notifications/")
        self.assertEqual(response.json()["count"], 1)

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.roles import Role
from core.testing import make_user

from .models import Task


class TaskViewTests(TestCase):
    def setUp(self):
        self.user = make_user(email="task-user@test.local", role=Role.SALES_AGENT)
        self.colleague = make_user(email="colleague@test.local", role=Role.SUPPORT_AGENT)
        self.client.force_login(self.user)

    def _make_task(self, **kwargs):
        defaults = {"title": "Do the thing", "created_by": self.user}
        defaults.update(kwargs)
        return Task.objects.create(**defaults)

    def test_create_task_notifies_assignee(self):
        self.client.post(reverse("tasks:add"), {
            "title": "Assigned task", "priority": "high", "status": "pending",
            "assigned_to": self.colleague.pk,
        })
        task = Task.objects.get(title="Assigned task")
        self.assertEqual(task.created_by, self.user)
        self.assertTrue(
            self.colleague.notifications.filter(title__icontains="task").exists()
        )

    def test_overdue_property(self):
        overdue = self._make_task(due_date=timezone.localdate() - timedelta(days=1))
        future = self._make_task(title="Later", due_date=timezone.localdate() + timedelta(days=1))
        done = self._make_task(
            title="Done", status=Task.Status.COMPLETED,
            due_date=timezone.localdate() - timedelta(days=1),
        )
        self.assertTrue(overdue.is_overdue)
        self.assertFalse(future.is_overdue)
        self.assertFalse(done.is_overdue)

    def test_comment_notifies_assignee(self):
        task = self._make_task(assigned_to=self.colleague)
        self.client.post(reverse("tasks:add_comment", args=[task.pk]), {"body": "Status?"})
        self.assertEqual(task.comments.count(), 1)
        self.assertTrue(
            self.colleague.notifications.filter(title__icontains="comment").exists()
        )

    def test_mine_filter(self):
        self._make_task(title="Mine", assigned_to=self.user)
        self._make_task(title="Theirs", assigned_to=self.colleague)
        response = self.client.get(reverse("tasks:list"), {"mine": "1"})
        self.assertContains(response, "Mine")
        self.assertNotContains(response, "Theirs")

    def test_all_roles_can_view_tasks(self):
        self.client.force_login(self.colleague)
        response = self.client.get(reverse("tasks:list"))
        self.assertEqual(response.status_code, 200)


class TaskAPITests(TestCase):
    def setUp(self):
        self.user = make_user(email="task-api@test.local", role=Role.MANAGER)
        self.client.force_login(self.user)

    def test_create_sets_created_by_and_comment_action(self):
        create = self.client.post("/api/v1/tasks/", {
            "title": "API task", "priority": "low", "status": "pending",
        })
        self.assertEqual(create.status_code, 201, create.content)
        pk = create.json()["id"]
        self.assertEqual(Task.objects.get(pk=pk).created_by, self.user)

        comment = self.client.post(f"/api/v1/tasks/{pk}/add_comment/", {"body": "hi"})
        self.assertEqual(comment.status_code, 201)

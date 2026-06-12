from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from accounts.models import User
from activity_logs.services import log_activity
from core.mixins import RolePermissionMixin
from notifications.services import notify

from .forms import TaskAttachmentForm, TaskCommentForm, TaskForm
from .models import Task


class TaskListView(RolePermissionMixin, ListView):
    module = "tasks"
    model = Task
    template_name = "tasks/list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("assigned_to", "created_by")
        if self.request.GET.get("mine"):
            qs = qs.filter(assigned_to=self.request.user)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        for param in ("status", "priority"):
            value = self.request.GET.get(param)
            if value:
                qs = qs.filter(**{param: value})
        assigned = self.request.GET.get("assigned_to")
        if assigned:
            qs = qs.filter(assigned_to_id=assigned)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Task.Status.choices
        ctx["priorities"] = Task.Priority.choices
        ctx["employees"] = User.objects.filter(is_active=True)
        return ctx


class TaskDetailView(RolePermissionMixin, DetailView):
    module = "tasks"
    model = Task
    template_name = "tasks/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["comments"] = self.object.comments.select_related("author")
        ctx["attachments"] = self.object.attachments.select_related("uploaded_by")
        ctx["comment_form"] = TaskCommentForm()
        ctx["attachment_form"] = TaskAttachmentForm()
        return ctx


class TaskCreateView(RolePermissionMixin, CreateView):
    module = "tasks"
    action = "modify"
    model = Task
    form_class = TaskForm
    template_name = "tasks/form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        log_activity(self.request.user, "create", f"Created task {self.object.title}", self.request)
        if self.object.assigned_to and self.object.assigned_to != self.request.user:
            notify(
                self.object.assigned_to,
                "Task assigned",
                f"Task '{self.object.title}' was assigned to you.",
                self.object.get_absolute_url(),
            )
        messages.success(self.request, "Task created.")
        return response


class TaskUpdateView(RolePermissionMixin, UpdateView):
    module = "tasks"
    action = "modify"
    model = Task
    form_class = TaskForm
    template_name = "tasks/form.html"

    def form_valid(self, form):
        previous_assignee_id = Task.objects.get(pk=self.object.pk).assigned_to_id
        response = super().form_valid(form)
        log_activity(self.request.user, "update", f"Updated task {self.object.title}", self.request)
        if (
            self.object.assigned_to_id
            and self.object.assigned_to_id != previous_assignee_id
            and self.object.assigned_to != self.request.user
        ):
            notify(
                self.object.assigned_to,
                "Task assigned",
                f"Task '{self.object.title}' was assigned to you.",
                self.object.get_absolute_url(),
            )
        messages.success(self.request, "Task updated.")
        return response


class TaskDeleteView(RolePermissionMixin, DeleteView):
    module = "tasks"
    action = "modify"
    model = Task
    template_name = "includes/confirm_delete.html"
    success_url = reverse_lazy("tasks:list")

    def form_valid(self, form):
        log_activity(self.request.user, "delete", f"Deleted task {self.object.title}", self.request)
        messages.success(self.request, "Task deleted.")
        return super().form_valid(form)


class TaskCommentCreateView(RolePermissionMixin, CreateView):
    module = "tasks"
    action = "modify"
    form_class = TaskCommentForm
    http_method_names = ["post"]

    def form_valid(self, form):
        task = get_object_or_404(Task, pk=self.kwargs["pk"])
        form.instance.task = task
        form.instance.author = self.request.user
        form.save()
        if task.assigned_to and task.assigned_to != self.request.user:
            notify(
                task.assigned_to,
                "New comment on your task",
                f"{self.request.user} commented on '{task.title}'.",
                task.get_absolute_url(),
            )
        return redirect("tasks:detail", pk=task.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Comment cannot be empty.")
        return redirect("tasks:detail", pk=self.kwargs["pk"])


class TaskAttachmentUploadView(RolePermissionMixin, CreateView):
    module = "tasks"
    action = "modify"
    form_class = TaskAttachmentForm
    http_method_names = ["post"]

    def form_valid(self, form):
        task = get_object_or_404(Task, pk=self.kwargs["pk"])
        form.instance.task = task
        form.instance.uploaded_by = self.request.user
        form.save()
        messages.success(self.request, "Attachment uploaded.")
        return redirect("tasks:detail", pk=task.pk)

    def form_invalid(self, form):
        for errors in form.errors.values():
            for error in errors:
                messages.error(self.request, error)
        return redirect("tasks:detail", pk=self.kwargs["pk"])

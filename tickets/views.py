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

from activity_logs.services import log_activity
from core.mixins import RolePermissionMixin
from notifications.services import notify

from .forms import TicketForm, TicketReplyForm
from .models import Ticket


class TicketListView(RolePermissionMixin, ListView):
    module = "tickets"
    model = Ticket
    template_name = "tickets/list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("customer", "assigned_to")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(ticket_number__icontains=q)
                | Q(subject__icontains=q)
                | Q(customer__first_name__icontains=q)
                | Q(customer__last_name__icontains=q)
            )
        for param in ("status", "priority"):
            value = self.request.GET.get(param)
            if value:
                qs = qs.filter(**{param: value})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Ticket.Status.choices
        ctx["priorities"] = Ticket.Priority.choices
        return ctx


class TicketDetailView(RolePermissionMixin, DetailView):
    module = "tickets"
    model = Ticket
    template_name = "tickets/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["replies"] = self.object.replies.select_related("author")
        ctx["reply_form"] = TicketReplyForm()
        return ctx


class TicketCreateView(RolePermissionMixin, CreateView):
    module = "tickets"
    action = "modify"
    model = Ticket
    form_class = TicketForm
    template_name = "tickets/form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        log_activity(
            self.request.user, "create",
            f"Created ticket {self.object.ticket_number}", self.request,
        )
        if self.object.assigned_to and self.object.assigned_to != self.request.user:
            notify(
                self.object.assigned_to,
                "Ticket assigned",
                f"Ticket {self.object.ticket_number} was assigned to you.",
                self.object.get_absolute_url(),
            )
        messages.success(self.request, f"Ticket {self.object.ticket_number} created.")
        return response


class TicketUpdateView(RolePermissionMixin, UpdateView):
    module = "tickets"
    action = "modify"
    model = Ticket
    form_class = TicketForm
    template_name = "tickets/form.html"

    def form_valid(self, form):
        old = Ticket.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        log_activity(
            self.request.user, "update",
            f"Updated ticket {self.object.ticket_number}", self.request,
        )
        if (
            self.object.assigned_to_id
            and self.object.assigned_to_id != old.assigned_to_id
            and self.object.assigned_to != self.request.user
        ):
            notify(
                self.object.assigned_to,
                "Ticket assigned",
                f"Ticket {self.object.ticket_number} was assigned to you.",
                self.object.get_absolute_url(),
            )
        elif self.object.status != old.status and self.object.assigned_to:
            notify(
                self.object.assigned_to,
                "Ticket status changed",
                f"Ticket {self.object.ticket_number} is now {self.object.get_status_display()}.",
                self.object.get_absolute_url(),
            )
        messages.success(self.request, "Ticket updated.")
        return response


class TicketDeleteView(RolePermissionMixin, DeleteView):
    module = "tickets"
    action = "modify"
    model = Ticket
    template_name = "includes/confirm_delete.html"
    success_url = reverse_lazy("tickets:list")

    def form_valid(self, form):
        log_activity(
            self.request.user, "delete",
            f"Deleted ticket {self.object.ticket_number}", self.request,
        )
        messages.success(self.request, "Ticket deleted.")
        return super().form_valid(form)


class TicketReplyCreateView(RolePermissionMixin, CreateView):
    module = "tickets"
    action = "modify"
    form_class = TicketReplyForm
    http_method_names = ["post"]

    def form_valid(self, form):
        ticket = get_object_or_404(Ticket, pk=self.kwargs["pk"])
        form.instance.ticket = ticket
        form.instance.author = self.request.user
        form.save()
        if ticket.assigned_to and ticket.assigned_to != self.request.user:
            notify(
                ticket.assigned_to,
                "New reply on ticket",
                f"{self.request.user} replied on {ticket.ticket_number}.",
                ticket.get_absolute_url(),
            )
        return redirect("tickets:detail", pk=ticket.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Reply cannot be empty.")
        return redirect("tickets:detail", pk=self.kwargs["pk"])

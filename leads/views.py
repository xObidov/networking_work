from django.contrib import messages
from django.db import transaction
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
from customers.models import Customer
from notifications.services import notify

from .forms import LeadForm, LeadNoteForm
from .models import Lead


class LeadListView(RolePermissionMixin, ListView):
    module = "leads"
    model = Lead
    template_name = "leads/list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("assigned_to", "converted_customer")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(email__icontains=q) | Q(company__icontains=q)
            )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        assigned = self.request.GET.get("assigned_to")
        if assigned:
            qs = qs.filter(assigned_to_id=assigned)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Lead.Status.choices
        ctx["employees"] = User.objects.filter(is_active=True)
        return ctx


class LeadDetailView(RolePermissionMixin, DetailView):
    module = "leads"
    model = Lead
    template_name = "leads/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["notes"] = self.object.lead_notes.select_related("author")
        ctx["note_form"] = LeadNoteForm()
        return ctx


class LeadCreateView(RolePermissionMixin, CreateView):
    module = "leads"
    action = "modify"
    model = Lead
    form_class = LeadForm
    template_name = "leads/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request.user, "create", f"Created lead {self.object.name}", self.request)
        if self.object.assigned_to and self.object.assigned_to != self.request.user:
            notify(
                self.object.assigned_to,
                "New lead assigned",
                f"Lead '{self.object.name}' was assigned to you.",
                self.object.get_absolute_url(),
            )
        messages.success(self.request, "Lead created.")
        return response


class LeadUpdateView(RolePermissionMixin, UpdateView):
    module = "leads"
    action = "modify"
    model = Lead
    form_class = LeadForm
    template_name = "leads/form.html"

    def form_valid(self, form):
        previous_assignee_id = Lead.objects.get(pk=self.object.pk).assigned_to_id
        response = super().form_valid(form)
        log_activity(self.request.user, "update", f"Updated lead {self.object.name}", self.request)
        if (
            self.object.assigned_to_id
            and self.object.assigned_to_id != previous_assignee_id
            and self.object.assigned_to != self.request.user
        ):
            notify(
                self.object.assigned_to,
                "Lead assigned to you",
                f"Lead '{self.object.name}' was assigned to you.",
                self.object.get_absolute_url(),
            )
        messages.success(self.request, "Lead updated.")
        return response


class LeadDeleteView(RolePermissionMixin, DeleteView):
    module = "leads"
    action = "modify"
    model = Lead
    template_name = "includes/confirm_delete.html"
    success_url = reverse_lazy("leads:list")

    def form_valid(self, form):
        log_activity(self.request.user, "delete", f"Deleted lead {self.object.name}", self.request)
        messages.success(self.request, "Lead deleted.")
        return super().form_valid(form)


class LeadNoteCreateView(RolePermissionMixin, CreateView):
    module = "leads"
    action = "modify"
    form_class = LeadNoteForm
    http_method_names = ["post"]

    def form_valid(self, form):
        lead = get_object_or_404(Lead, pk=self.kwargs["pk"])
        form.instance.lead = lead
        form.instance.author = self.request.user
        form.save()
        return redirect("leads:detail", pk=lead.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Note cannot be empty.")
        return redirect("leads:detail", pk=self.kwargs["pk"])


def convert_lead(request, pk):
    """Convert a won lead into a customer (POST only, atomic)."""
    from core.roles import has_module_permission

    if request.method != "POST":
        return redirect("leads:detail", pk=pk)
    if not (
        request.user.is_authenticated
        and has_module_permission(request.user, "leads", "modify")
    ):
        messages.error(request, "You do not have permission to convert leads.")
        return redirect("leads:list")

    lead = get_object_or_404(Lead, pk=pk)
    if lead.is_converted:
        messages.info(request, "This lead has already been converted.")
        return redirect("customers:detail", pk=lead.converted_customer_id)

    name_parts = lead.name.split(maxsplit=1)
    with transaction.atomic():
        customer, created = Customer.objects.get_or_create(
            email=lead.email or f"lead{lead.pk}@unknown.local",
            defaults={
                "first_name": name_parts[0],
                "last_name": name_parts[1] if len(name_parts) > 1 else "",
                "phone": lead.phone,
                "company": lead.company,
                "notes": lead.notes,
                "status": Customer.Status.ACTIVE,
                "owner": lead.assigned_to or request.user,
            },
        )
        lead.converted_customer = customer
        lead.status = Lead.Status.WON
        lead.save(update_fields=["converted_customer", "status", "updated_at"])

    log_activity(request.user, "convert", f"Converted lead {lead.name} to customer", request)
    messages.success(request, f"Lead converted to customer {customer.full_name}.")
    return redirect("customers:detail", pk=customer.pk)

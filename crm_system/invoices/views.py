from django.contrib import messages
from django.db.models import Q
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

from .forms import InvoiceForm
from .models import Invoice
from .pdf import render_invoice_pdf


class InvoiceListView(RolePermissionMixin, ListView):
    module = "invoices"
    model = Invoice
    template_name = "invoices/list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("customer", "deal")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(invoice_number__icontains=q)
                | Q(customer__first_name__icontains=q)
                | Q(customer__last_name__icontains=q)
            )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Invoice.Status.choices
        return ctx


class InvoiceDetailView(RolePermissionMixin, DetailView):
    module = "invoices"
    model = Invoice
    template_name = "invoices/detail.html"


class InvoiceCreateView(RolePermissionMixin, CreateView):
    module = "invoices"
    action = "modify"
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoices/form.html"

    def form_valid(self, form):
        form.instance.issued_by = self.request.user
        response = super().form_valid(form)
        log_activity(
            self.request.user, "create",
            f"Generated invoice {self.object.invoice_number}", self.request,
        )
        messages.success(self.request, f"Invoice {self.object.invoice_number} created.")
        return response


class InvoiceUpdateView(RolePermissionMixin, UpdateView):
    module = "invoices"
    action = "modify"
    model = Invoice
    form_class = InvoiceForm
    template_name = "invoices/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            self.request.user, "update",
            f"Updated invoice {self.object.invoice_number}", self.request,
        )
        messages.success(self.request, "Invoice updated.")
        return response


class InvoiceDeleteView(RolePermissionMixin, DeleteView):
    module = "invoices"
    action = "modify"
    model = Invoice
    template_name = "includes/confirm_delete.html"
    success_url = reverse_lazy("invoices:list")

    def form_valid(self, form):
        log_activity(
            self.request.user, "delete",
            f"Deleted invoice {self.object.invoice_number}", self.request,
        )
        messages.success(self.request, "Invoice deleted.")
        return super().form_valid(form)


class InvoicePdfView(RolePermissionMixin, DetailView):
    module = "invoices"
    model = Invoice

    def render_to_response(self, context, **kwargs):
        return render_invoice_pdf(self.object)

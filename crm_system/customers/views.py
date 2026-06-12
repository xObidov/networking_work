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

from activity_logs.models import ActivityLog
from activity_logs.services import log_activity
from core.mixins import RolePermissionMixin

from .forms import CustomerDocumentForm, CustomerForm
from .models import Customer, Tag


class CustomerListView(RolePermissionMixin, ListView):
    module = "customers"
    model = Customer
    template_name = "customers/list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("owner")
            .prefetch_related("tags")
        )
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(company__icontains=q)
            )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        tag = self.request.GET.get("tag")
        if tag:
            qs = qs.filter(tags__id=tag)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Customer.Status.choices
        ctx["all_tags"] = Tag.objects.all()
        return ctx


class CustomerDetailView(RolePermissionMixin, DetailView):
    module = "customers"
    model = Customer
    template_name = "customers/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        customer = self.object
        # Timeline: deals, tickets, invoices and audit entries for this customer
        ctx["deals"] = customer.deals.all()
        ctx["tickets"] = customer.tickets.all()
        ctx["invoices"] = customer.invoices.all()
        ctx["documents"] = customer.documents.select_related("uploaded_by")
        ctx["document_form"] = CustomerDocumentForm()
        ctx["activities"] = ActivityLog.objects.filter(
            description__icontains=customer.full_name
        )[:20]
        return ctx


class CustomerCreateView(RolePermissionMixin, CreateView):
    module = "customers"
    action = "modify"
    model = Customer
    form_class = CustomerForm
    template_name = "customers/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            self.request.user, "create",
            f"Created customer {self.object.full_name}", self.request,
        )
        messages.success(self.request, "Customer created.")
        return response


class CustomerUpdateView(RolePermissionMixin, UpdateView):
    module = "customers"
    action = "modify"
    model = Customer
    form_class = CustomerForm
    template_name = "customers/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            self.request.user, "update",
            f"Updated customer {self.object.full_name}", self.request,
        )
        messages.success(self.request, "Customer updated.")
        return response


class CustomerDeleteView(RolePermissionMixin, DeleteView):
    module = "customers"
    action = "modify"
    model = Customer
    template_name = "includes/confirm_delete.html"
    success_url = reverse_lazy("customers:list")

    def form_valid(self, form):
        log_activity(
            self.request.user, "delete",
            f"Deleted customer {self.object.full_name}", self.request,
        )
        messages.success(self.request, "Customer deleted.")
        return super().form_valid(form)


class CustomerDocumentUploadView(RolePermissionMixin, CreateView):
    module = "customers"
    action = "modify"
    form_class = CustomerDocumentForm
    http_method_names = ["post"]

    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs["pk"])
        form.instance.customer = customer
        form.instance.uploaded_by = self.request.user
        form.save()
        messages.success(self.request, "Document uploaded.")
        return redirect("customers:detail", pk=customer.pk)

    def form_invalid(self, form):
        for errors in form.errors.values():
            for error in errors:
                messages.error(self.request, error)
        return redirect("customers:detail", pk=self.kwargs["pk"])

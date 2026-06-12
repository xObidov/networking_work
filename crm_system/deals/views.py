import json

from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from activity_logs.services import log_activity
from core.mixins import RolePermissionMixin
from core.roles import has_module_permission
from notifications.services import notify

from .forms import DealForm
from .models import Deal


class DealKanbanView(RolePermissionMixin, TemplateView):
    """Kanban board: one column per stage, cards draggable via AJAX."""

    module = "deals"
    template_name = "deals/kanban.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        deals = Deal.objects.select_related("customer", "owner")
        columns = []
        for stage, label in Deal.Stage.choices:
            stage_deals = [d for d in deals if d.stage == stage]
            columns.append({
                "stage": stage,
                "label": label,
                "deals": stage_deals,
                "total": sum(d.value for d in stage_deals),
            })
        ctx["columns"] = columns
        ctx["won_total"] = (
            Deal.objects.filter(stage=Deal.Stage.WON).aggregate(s=Sum("value"))["s"] or 0
        )
        return ctx


class DealListView(RolePermissionMixin, ListView):
    module = "deals"
    model = Deal
    template_name = "deals/list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("customer", "owner")
        stage = self.request.GET.get("stage")
        if stage:
            qs = qs.filter(stage=stage)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["stages"] = Deal.Stage.choices
        return ctx


class DealDetailView(RolePermissionMixin, DetailView):
    module = "deals"
    model = Deal
    template_name = "deals/detail.html"


class DealCreateView(RolePermissionMixin, CreateView):
    module = "deals"
    action = "modify"
    model = Deal
    form_class = DealForm
    template_name = "deals/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request.user, "create", f"Created deal {self.object.name}", self.request)
        if self.object.owner and self.object.owner != self.request.user:
            notify(
                self.object.owner,
                "New deal",
                f"Deal '{self.object.name}' (${self.object.value}) was assigned to you.",
                self.object.get_absolute_url(),
            )
        messages.success(self.request, "Deal created.")
        return response


class DealUpdateView(RolePermissionMixin, UpdateView):
    module = "deals"
    action = "modify"
    model = Deal
    form_class = DealForm
    template_name = "deals/form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request.user, "update", f"Updated deal {self.object.name}", self.request)
        messages.success(self.request, "Deal updated.")
        return response


class DealDeleteView(RolePermissionMixin, DeleteView):
    module = "deals"
    action = "modify"
    model = Deal
    template_name = "includes/confirm_delete.html"
    success_url = reverse_lazy("deals:kanban")

    def form_valid(self, form):
        log_activity(self.request.user, "delete", f"Deleted deal {self.object.name}", self.request)
        messages.success(self.request, "Deal deleted.")
        return super().form_valid(form)


@require_POST
def update_stage(request, pk):
    """AJAX endpoint used by the kanban board drag-and-drop."""
    if not (
        request.user.is_authenticated
        and has_module_permission(request.user, "deals", "modify")
    ):
        return JsonResponse({"error": "forbidden"}, status=403)

    deal = get_object_or_404(Deal, pk=pk)
    try:
        stage = json.loads(request.body).get("stage")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON"}, status=400)
    if stage not in Deal.Stage.values:
        return JsonResponse({"error": "invalid stage"}, status=400)

    old_stage = deal.get_stage_display()
    deal.stage = stage
    deal.save(update_fields=["stage", "updated_at"])
    log_activity(
        request.user, "status_change",
        f"Moved deal {deal.name} from {old_stage} to {deal.get_stage_display()}",
        request,
    )
    return JsonResponse({"ok": True, "stage": stage})

from core.mixins import RolePermissionMixin
from django.views.generic import ListView

from .models import ActivityLog


class ActivityLogListView(RolePermissionMixin, ListView):
    module = "activity_logs"
    model = ActivityLog
    template_name = "activity_logs/list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related("user")
        action = self.request.GET.get("action")
        if action:
            qs = qs.filter(action=action)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(description__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = ActivityLog.Action.choices
        return ctx

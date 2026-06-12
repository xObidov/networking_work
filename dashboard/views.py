"""Dashboard: headline KPIs + JSON endpoints feeding the Chart.js widgets."""
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import User
from activity_logs.models import ActivityLog
from customers.models import Customer
from deals.models import Deal
from leads.models import Lead
from tasks.models import Task


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        ctx["total_customers"] = Customer.objects.count()
        ctx["total_leads"] = Lead.objects.count()
        ctx["total_deals"] = Deal.objects.count()
        ctx["total_revenue"] = (
            Deal.objects.filter(stage=Deal.Stage.WON).aggregate(s=Sum("value"))["s"] or 0
        )
        ctx["active_tasks"] = Task.objects.filter(
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
        ).count()
        ctx["new_leads"] = Lead.objects.filter(created_at__gte=month_start).count()
        ctx["recent_activities"] = ActivityLog.objects.select_related("user")[:10]
        ctx["my_tasks"] = (
            Task.objects.filter(
                assigned_to=self.request.user,
                status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS],
            ).order_by("due_date")[:5]
        )
        return ctx


def _month_labels(n=12):
    """Last n month starts, oldest first."""
    current = timezone.now().date().replace(day=1)
    months = []
    for _ in range(n):
        months.append(current)
        current = (current - timedelta(days=1)).replace(day=1)
    return list(reversed(months))


def monthly_revenue_data(request):
    """Won deal value per month for the last 12 months."""
    if not request.user.is_authenticated:
        return JsonResponse({}, status=403)
    months = _month_labels()
    rows = (
        Deal.objects.filter(stage=Deal.Stage.WON, created_at__date__gte=months[0])
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("value"))
    )
    by_month = {r["month"].date(): float(r["total"]) for r in rows}
    return JsonResponse({
        "labels": [m.strftime("%b %Y") for m in months],
        "data": [by_month.get(m, 0) for m in months],
    })


def lead_conversion_data(request):
    """Lead counts per status — drives the conversion funnel doughnut."""
    if not request.user.is_authenticated:
        return JsonResponse({}, status=403)
    rows = Lead.objects.values("status").annotate(n=Count("id"))
    by_status = {r["status"]: r["n"] for r in rows}
    labels, data = [], []
    for status, label in Lead.Status.choices:
        labels.append(label)
        data.append(by_status.get(status, 0))
    total = sum(data)
    won = by_status.get(Lead.Status.WON, 0)
    return JsonResponse({
        "labels": labels,
        "data": data,
        "conversion_rate": round(won * 100 / total, 1) if total else 0,
    })


def sales_growth_data(request):
    """New customers per month — customer growth curve."""
    if not request.user.is_authenticated:
        return JsonResponse({}, status=403)
    months = _month_labels()
    rows = (
        Customer.objects.filter(created_at__date__gte=months[0])
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(n=Count("id"))
    )
    by_month = {r["month"].date(): r["n"] for r in rows}
    return JsonResponse({
        "labels": [m.strftime("%b %Y") for m in months],
        "data": [by_month.get(m, 0) for m in months],
    })


def employee_performance_data(request):
    """Won-deal revenue per employee."""
    if not request.user.is_authenticated:
        return JsonResponse({}, status=403)
    rows = (
        Deal.objects.filter(stage=Deal.Stage.WON, owner__isnull=False)
        .values("owner__first_name", "owner__last_name", "owner__email")
        .annotate(total=Sum("value"), count=Count("id"))
        .order_by("-total")[:10]
    )
    labels = [
        (f"{r['owner__first_name']} {r['owner__last_name']}".strip() or r["owner__email"])
        for r in rows
    ]
    return JsonResponse({
        "labels": labels,
        "data": [float(r["total"]) for r in rows],
    })

from django.http import Http404
from django.views.generic import TemplateView

from core.mixins import RolePermissionMixin

from .services import REPORTS, export_excel, export_pdf


class ReportIndexView(RolePermissionMixin, TemplateView):
    module = "reports"
    template_name = "reports/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["reports"] = [
            {"key": key, "title": builder()["title"]}
            for key, builder in REPORTS.items()
        ]
        return ctx


class ReportDetailView(RolePermissionMixin, TemplateView):
    module = "reports"
    template_name = "reports/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        key = self.kwargs["key"]
        builder = REPORTS.get(key)
        if builder is None:
            raise Http404
        ctx["report"] = builder()
        ctx["key"] = key
        return ctx


class ReportExportView(RolePermissionMixin, TemplateView):
    module = "reports"

    def get(self, request, *args, **kwargs):
        builder = REPORTS.get(self.kwargs["key"])
        if builder is None:
            raise Http404
        report = builder()
        if self.kwargs["fmt"] == "xlsx":
            return export_excel(report)
        if self.kwargs["fmt"] == "pdf":
            return export_pdf(report)
        raise Http404

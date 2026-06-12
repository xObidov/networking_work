"""Report dataset builders + PDF/Excel exporters."""
from io import BytesIO

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font
from xhtml2pdf import pisa

from accounts.models import User
from customers.models import Customer
from deals.models import Deal
from invoices.models import Invoice
from leads.models import Lead
from tasks.models import Task


def customer_report():
    return {
        "title": "Customer Report",
        "headers": ["Name", "Email", "Company", "Status", "Country", "Created"],
        "rows": [
            [c.full_name, c.email, c.company, c.get_status_display(), c.country,
             c.created_at.strftime("%Y-%m-%d")]
            for c in Customer.objects.all()
        ],
    }


def lead_report():
    return {
        "title": "Lead Report",
        "headers": ["Name", "Company", "Source", "Status", "Assigned To", "Created"],
        "rows": [
            [l.name, l.company, l.get_source_display(), l.get_status_display(),
             str(l.assigned_to or "—"), l.created_at.strftime("%Y-%m-%d")]
            for l in Lead.objects.select_related("assigned_to")
        ],
    }


def deal_report():
    return {
        "title": "Deal Report",
        "headers": ["Deal", "Customer", "Value", "Stage", "Expected Close", "Owner"],
        "rows": [
            [d.name, d.customer.full_name, float(d.value), d.get_stage_display(),
             str(d.expected_close_date or "—"), str(d.owner or "—")]
            for d in Deal.objects.select_related("customer", "owner")
        ],
    }


def revenue_report():
    return {
        "title": "Revenue Report",
        "headers": ["Invoice", "Customer", "Amount", "Tax", "Total", "Status", "Due"],
        "rows": [
            [i.invoice_number, i.customer.full_name, float(i.amount),
             float(i.tax_amount), float(i.total_amount), i.get_status_display(),
             str(i.due_date or "—")]
            for i in Invoice.objects.select_related("customer")
        ],
    }


def task_report():
    return {
        "title": "Task Report",
        "headers": ["Title", "Assigned To", "Priority", "Status", "Due Date"],
        "rows": [
            [t.title, str(t.assigned_to or "—"), t.get_priority_display(),
             t.get_status_display(), str(t.due_date or "—")]
            for t in Task.objects.select_related("assigned_to")
        ],
    }


def employee_report():
    rows = []
    for user in User.objects.filter(is_active=True):
        won = user.deals.filter(stage=Deal.Stage.WON).aggregate(
            total=Sum("value"), n=Count("id")
        )
        rows.append([
            user.get_full_name() or user.email,
            user.get_role_display(),
            user.leads.count(),
            won["n"] or 0,
            float(won["total"] or 0),
            user.tasks.filter(status=Task.Status.COMPLETED).count(),
        ])
    return {
        "title": "Employee Performance Report",
        "headers": ["Employee", "Role", "Leads", "Deals Won", "Revenue", "Tasks Done"],
        "rows": rows,
    }


REPORTS = {
    "customers": customer_report,
    "leads": lead_report,
    "deals": deal_report,
    "revenue": revenue_report,
    "tasks": task_report,
    "employees": employee_report,
}


def export_excel(report: dict) -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = report["title"][:31]
    ws.append(report["headers"])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in report["rows"]:
        ws.append(row)
    buffer = BytesIO()
    wb.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    filename = report["title"].lower().replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return response


def export_pdf(report: dict) -> HttpResponse:
    html = render_to_string(
        "reports/pdf.html", {"report": report, "generated_at": timezone.now()}
    )
    buffer = BytesIO()
    result = pisa.CreatePDF(html, dest=buffer)
    if result.err:
        return HttpResponse("Failed to generate PDF", status=500)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    filename = report["title"].lower().replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return response

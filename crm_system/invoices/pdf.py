"""HTML → PDF rendering for invoices (xhtml2pdf, pure Python, no services)."""
from io import BytesIO

from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def render_invoice_pdf(invoice) -> HttpResponse:
    html = render_to_string("invoices/pdf.html", {"invoice": invoice})
    buffer = BytesIO()
    result = pisa.CreatePDF(html, dest=buffer)
    if result.err:
        return HttpResponse("Failed to generate PDF", status=500)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{invoice.invoice_number}.pdf"'
    )
    return response

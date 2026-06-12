from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "customer", "amount", "tax_rate", "status", "due_date"]
    list_filter = ["status"]
    search_fields = ["invoice_number", "customer__first_name", "customer__last_name"]

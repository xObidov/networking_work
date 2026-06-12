from django.contrib import admin

from .models import Deal


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ["name", "customer", "value", "stage", "expected_close_date", "owner"]
    list_filter = ["stage"]
    search_fields = ["name", "customer__first_name", "customer__last_name"]

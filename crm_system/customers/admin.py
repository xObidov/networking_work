from django.contrib import admin

from .models import Customer, CustomerDocument, Tag


class CustomerDocumentInline(admin.TabularInline):
    model = CustomerDocument
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "company", "status", "owner", "created_at"]
    list_filter = ["status", "country"]
    search_fields = ["first_name", "last_name", "email", "company"]
    inlines = [CustomerDocumentInline]
    filter_horizontal = ["tags"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "color"]

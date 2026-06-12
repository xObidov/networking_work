from django.contrib import admin

from .models import Lead, LeadNote


class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 0


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "status", "source", "assigned_to", "created_at"]
    list_filter = ["status", "source"]
    search_fields = ["name", "email", "company"]
    inlines = [LeadNoteInline]

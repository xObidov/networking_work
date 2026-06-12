from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "description", "ip_address", "created_at"]
    list_filter = ["action"]
    search_fields = ["description", "user__email"]
    readonly_fields = ["user", "action", "description", "ip_address", "created_at", "updated_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

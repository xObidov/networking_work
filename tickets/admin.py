from django.contrib import admin

from .models import Ticket, TicketReply


class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["ticket_number", "subject", "customer", "priority", "status", "assigned_to"]
    list_filter = ["status", "priority"]
    search_fields = ["ticket_number", "subject"]
    inlines = [TicketReplyInline]

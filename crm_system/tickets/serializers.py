from rest_framework import serializers

from .models import Ticket, TicketReply


class TicketReplySerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = TicketReply
        fields = ["id", "body", "author", "author_email", "created_at"]
        read_only_fields = ["author", "created_at"]


class TicketSerializer(serializers.ModelSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "ticket_number", "customer", "customer_name", "subject",
            "description", "priority", "status", "assigned_to", "created_by",
            "replies", "created_at", "updated_at",
        ]
        read_only_fields = ["ticket_number", "created_by", "created_at", "updated_at"]

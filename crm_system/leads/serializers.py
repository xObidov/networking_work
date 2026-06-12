from rest_framework import serializers

from .models import Lead, LeadNote


class LeadNoteSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = LeadNote
        fields = ["id", "body", "author", "author_email", "created_at"]
        read_only_fields = ["author", "created_at"]


class LeadSerializer(serializers.ModelSerializer):
    lead_notes = LeadNoteSerializer(many=True, read_only=True)
    assigned_to_name = serializers.CharField(
        source="assigned_to.get_full_name", read_only=True
    )

    class Meta:
        model = Lead
        fields = [
            "id", "name", "email", "phone", "company", "source", "status",
            "assigned_to", "assigned_to_name", "notes", "converted_customer",
            "lead_notes", "created_at", "updated_at",
        ]
        read_only_fields = ["converted_customer", "created_at", "updated_at"]

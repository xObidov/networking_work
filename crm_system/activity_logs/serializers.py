from rest_framework import serializers

from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ActivityLog
        fields = ["id", "user", "user_email", "action", "description", "ip_address", "created_at"]
        read_only_fields = fields

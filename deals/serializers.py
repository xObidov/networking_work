from rest_framework import serializers

from .models import Deal


class DealSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta:
        model = Deal
        fields = [
            "id", "name", "customer", "customer_name", "value", "stage",
            "description", "expected_close_date", "owner", "owner_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

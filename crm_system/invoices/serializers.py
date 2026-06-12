from rest_framework import serializers

from .models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "customer", "customer_name", "deal",
            "amount", "tax_rate", "tax_amount", "total_amount", "status",
            "due_date", "issued_by", "created_at", "updated_at",
        ]
        read_only_fields = ["invoice_number", "issued_by", "created_at", "updated_at"]

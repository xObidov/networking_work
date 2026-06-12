from rest_framework import viewsets

from core.permissions import RoleModulePermission

from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related("customer", "deal")
    serializer_class = InvoiceSerializer
    permission_classes = [RoleModulePermission]
    module = "invoices"
    filterset_fields = ["status", "customer"]
    search_fields = ["invoice_number"]
    ordering_fields = ["created_at", "amount", "due_date"]

    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)

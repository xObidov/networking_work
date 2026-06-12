from rest_framework import viewsets

from core.permissions import RoleModulePermission

from .models import Deal
from .serializers import DealSerializer


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.select_related("customer", "owner")
    serializer_class = DealSerializer
    permission_classes = [RoleModulePermission]
    module = "deals"
    filterset_fields = ["stage", "customer", "owner"]
    search_fields = ["name", "customer__first_name", "customer__last_name"]
    ordering_fields = ["created_at", "value", "expected_close_date"]

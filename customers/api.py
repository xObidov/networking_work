from rest_framework import viewsets

from core.permissions import RoleModulePermission

from .models import Customer, Tag
from .serializers import CustomerSerializer, TagSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.select_related("owner").prefetch_related("tags", "documents")
    serializer_class = CustomerSerializer
    permission_classes = [RoleModulePermission]
    module = "customers"
    filterset_fields = ["status", "city", "country", "owner"]
    search_fields = ["first_name", "last_name", "email", "company"]
    ordering_fields = ["created_at", "last_name", "company"]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [RoleModulePermission]
    module = "customers"

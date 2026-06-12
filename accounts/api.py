from rest_framework import viewsets

from core.permissions import RoleModulePermission

from .models import User
from .serializers import UserCreateSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """User administration — restricted to Super Admin / Admin roles."""

    queryset = User.objects.all()
    permission_classes = [RoleModulePermission]
    module = "users"
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at", "email"]

    def get_serializer_class(self):
        return UserCreateSerializer if self.action == "create" else UserSerializer

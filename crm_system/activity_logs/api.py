from rest_framework import viewsets

from core.permissions import RoleModulePermission

from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log is read-only over the API."""

    queryset = ActivityLog.objects.select_related("user")
    serializer_class = ActivityLogSerializer
    permission_classes = [RoleModulePermission]
    module = "activity_logs"
    filterset_fields = ["action", "user"]
    search_fields = ["description"]

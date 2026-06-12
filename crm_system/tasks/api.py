from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import RoleModulePermission

from .models import Task
from .serializers import TaskCommentSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related("assigned_to", "created_by")
    serializer_class = TaskSerializer
    permission_classes = [RoleModulePermission]
    module = "tasks"
    filterset_fields = ["status", "priority", "assigned_to"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "due_date", "priority"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def add_comment(self, request, pk=None):
        task = self.get_object()
        serializer = TaskCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

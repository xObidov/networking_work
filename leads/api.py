from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import RoleModulePermission

from .models import Lead
from .serializers import LeadNoteSerializer, LeadSerializer


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.select_related("assigned_to", "converted_customer")
    serializer_class = LeadSerializer
    permission_classes = [RoleModulePermission]
    module = "leads"
    filterset_fields = ["status", "source", "assigned_to"]
    search_fields = ["name", "email", "company"]
    ordering_fields = ["created_at", "name"]

    @action(detail=True, methods=["post"])
    def add_note(self, request, pk=None):
        lead = self.get_object()
        serializer = LeadNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(lead=lead, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import RoleModulePermission

from .models import Ticket
from .serializers import TicketReplySerializer, TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("customer", "assigned_to")
    serializer_class = TicketSerializer
    permission_classes = [RoleModulePermission]
    module = "tickets"
    filterset_fields = ["status", "priority", "assigned_to", "customer"]
    search_fields = ["ticket_number", "subject"]
    ordering_fields = ["created_at", "priority"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

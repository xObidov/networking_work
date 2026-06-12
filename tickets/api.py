import os

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from accounts.models import User
from activity_logs.services import log_activity
from core.permissions import RoleModulePermission
from core.roles import Role
from customers.models import Customer
from notifications.services import notify

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


class ContactFormSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    message = serializers.CharField(max_length=5000)


class ContactFormThrottle(AnonRateThrottle):
    rate = "10/min"


class ContactFormView(APIView):
    """
    Public endpoint for the company website's contact form.

    Anonymous, but optionally protected by a shared secret: when the
    CONTACT_API_KEY env var is set, requests must send the same value in
    the X-Contact-Key header. Creates (or reuses) a Customer by email and
    opens a support Ticket, then notifies admins and support agents.
    """

    authentication_classes = []  # no session auth -> no CSRF requirement
    permission_classes = [AllowAny]
    throttle_classes = [ContactFormThrottle]

    def post(self, request):
        required_key = os.getenv("CONTACT_API_KEY")
        if required_key and request.headers.get("X-Contact-Key") != required_key:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ContactFormSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        name_parts = data["name"].split(maxsplit=1)
        customer, _ = Customer.objects.get_or_create(
            email=data["email"],
            defaults={
                "first_name": name_parts[0],
                "last_name": name_parts[1] if len(name_parts) > 1 else "",
                "phone": data.get("phone", ""),
                "status": Customer.Status.PROSPECT,
            },
        )
        ticket = Ticket.objects.create(
            customer=customer,
            subject=f"Aloqa formasi: {data['name']}"[:200],
            description=data["message"],
            priority=Ticket.Priority.MEDIUM,
        )
        recipients = User.objects.filter(
            is_active=True,
            role__in=[Role.SUPER_ADMIN, Role.ADMIN, Role.SUPPORT_AGENT],
        )
        for user in recipients:
            notify(
                user,
                "Yangi murojaat (saytdan)",
                f"{data['name']} ({data['email']}) aloqa formasidan murojaat qoldirdi.",
                ticket.get_absolute_url(),
            )
        log_activity(
            None, "create",
            f"Contact form ticket {ticket.ticket_number} from {data['email']}",
            request,
        )
        return Response(
            {"ok": True, "ticket_number": ticket.ticket_number},
            status=status.HTTP_201_CREATED,
        )

"""REST API v1 router. Every app registers its ViewSets here."""
from rest_framework.routers import DefaultRouter

from accounts.api import UserViewSet
from activity_logs.api import ActivityLogViewSet
from customers.api import CustomerViewSet, TagViewSet
from deals.api import DealViewSet
from invoices.api import InvoiceViewSet
from leads.api import LeadViewSet
from notifications.api import NotificationViewSet
from tasks.api import TaskViewSet
from tickets.api import TicketViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("customers", CustomerViewSet, basename="customer")
router.register("tags", TagViewSet, basename="tag")
router.register("leads", LeadViewSet, basename="lead")
router.register("deals", DealViewSet, basename="deal")
router.register("tasks", TaskViewSet, basename="task")
router.register("tickets", TicketViewSet, basename="ticket")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("activity-logs", ActivityLogViewSet, basename="activitylog")

urlpatterns = router.urls

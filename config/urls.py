"""Root URL configuration: web UI, REST API v1 and JWT token endpoints."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),  # set_language view
    # ---- Public landing page (ommaviy bosh sahifa) ----
    path("", TemplateView.as_view(template_name="public/home.html"), name="home"),
    # ---- Web UI (CRM) ----
    path("dashboard/", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("customers/", include("customers.urls")),
    path("leads/", include("leads.urls")),
    path("deals/", include("deals.urls")),
    path("tasks/", include("tasks.urls")),
    path("tickets/", include("tickets.urls")),
    path("invoices/", include("invoices.urls")),
    path("reports/", include("reports.urls")),
    path("notifications/", include("notifications.urls")),
    path("activity/", include("activity_logs.urls")),
    # ---- REST API ----
    path("api/v1/", include("core.api_urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

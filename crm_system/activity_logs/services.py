"""Single entry point other apps use to record audit events."""
from .models import ActivityLog


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_activity(user, action, description, request=None):
    ActivityLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        description=description[:500],
        ip_address=get_client_ip(request) if request is not None else None,
    )

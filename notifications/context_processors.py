"""Puts the unread badge count + latest items in every template context."""


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {}
    qs = request.user.notifications.filter(is_read=False)
    return {
        "unread_count": qs.count(),
        "recent_notifications": qs[:5],
    }

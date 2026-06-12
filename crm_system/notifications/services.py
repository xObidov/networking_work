"""Helper other apps call to create notifications."""
from .models import Notification


def notify(user, title, message="", link=""):
    if user is None:
        return None
    return Notification.objects.create(
        user=user, title=title, message=message, link=link
    )

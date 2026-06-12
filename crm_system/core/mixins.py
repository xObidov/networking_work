"""Reusable view mixins for the web UI."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .roles import has_module_permission


class RolePermissionMixin(LoginRequiredMixin):
    """
    Class-based-view guard. Set on each view:

        module = "customers"
        action = "view"  # or "modify"
    """

    module: str = ""
    action: str = "view"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not has_module_permission(request.user, self.module, self.action):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SuccessMessageMixin:
    """Adds a flash message after a successful form submission."""

    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response

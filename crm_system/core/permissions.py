"""DRF permission classes backed by the same RBAC matrix as the web UI."""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .roles import has_module_permission


class RoleModulePermission(BasePermission):
    """
    ViewSets declare `module = "<name>"`; read methods need "view",
    write methods need "modify".
    """

    def has_permission(self, request, view):
        module = getattr(view, "module", "")
        action = "view" if request.method in SAFE_METHODS else "modify"
        return has_module_permission(request.user, module, action)

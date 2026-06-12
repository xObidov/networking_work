"""
Central RBAC definition.

A user's role is a single field on the User model. Every view (web and API)
declares which roles may use it; the helpers below do the checking so the
policy lives in exactly one place.
"""
from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    SALES_AGENT = "sales_agent", "Sales Agent"
    SUPPORT_AGENT = "support_agent", "Support Agent"


# Convenience groups used by views.
ALL_ROLES = [r for r, _ in Role.choices]
MANAGEMENT = [Role.SUPER_ADMIN, Role.ADMIN, Role.MANAGER]
SALES = MANAGEMENT + [Role.SALES_AGENT]
SUPPORT = MANAGEMENT + [Role.SUPPORT_AGENT]

# Per-module access matrix: which roles can view / modify each domain.
ROLE_MATRIX = {
    "customers": {"view": ALL_ROLES, "modify": SALES},
    "leads": {"view": SALES, "modify": SALES},
    "deals": {"view": SALES, "modify": SALES},
    "tasks": {"view": ALL_ROLES, "modify": ALL_ROLES},
    "tickets": {"view": SUPPORT, "modify": SUPPORT},
    "invoices": {"view": MANAGEMENT, "modify": MANAGEMENT},
    "reports": {"view": MANAGEMENT, "modify": MANAGEMENT},
    "activity_logs": {"view": [Role.SUPER_ADMIN, Role.ADMIN], "modify": []},
    "users": {"view": [Role.SUPER_ADMIN, Role.ADMIN], "modify": [Role.SUPER_ADMIN]},
}


def has_module_permission(user, module: str, action: str = "view") -> bool:
    """True if `user`'s role grants `action` ("view"/"modify") on `module`."""
    if not user.is_authenticated:
        return False
    if user.role == Role.SUPER_ADMIN:
        return True
    allowed = ROLE_MATRIX.get(module, {}).get(action, [])
    return user.role in allowed

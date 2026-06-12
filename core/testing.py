"""Shared helpers for the test suite."""
from django.contrib.auth import get_user_model

from core.roles import Role

User = get_user_model()

PASSWORD = "Str0ng-test-pass!"


def make_user(email="user@test.local", role=Role.SALES_AGENT, **kwargs):
    return User.objects.create_user(
        email=email, password=PASSWORD, role=role,
        first_name=kwargs.pop("first_name", "Test"),
        last_name=kwargs.pop("last_name", "User"),
        **kwargs,
    )


def make_admin(email="admin@test.local"):
    return make_user(email=email, role=Role.ADMIN)


def make_customer(**kwargs):
    from customers.models import Customer

    defaults = {
        "first_name": "Acme",
        "last_name": "Contact",
        "email": f"contact{Customer.objects.count()}@acme.test",
        "company": "Acme Corp",
    }
    defaults.update(kwargs)
    return Customer.objects.create(**defaults)

"""Custom user model with role-based access control and email verification."""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from core.models import TimeStampedModel
from core.roles import Role


class UserManager(BaseUserManager):
    """Email is the login identifier; username is not used."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.SUPER_ADMIN)
        extra_fields.setdefault("is_email_verified", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel):
    username = None
    email = models.EmailField("email address", unique=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.SALES_AGENT, db_index=True
    )
    phone = models.CharField(max_length=30, blank=True)
    position = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.get_full_name() or self.email

    @property
    def initials(self):
        name = self.get_full_name() or self.email
        parts = name.split()
        return "".join(p[0].upper() for p in parts[:2])

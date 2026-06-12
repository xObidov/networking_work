"""Authentication and profile views (web UI)."""
from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from activity_logs.services import log_activity

from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import User
from .tokens import make_verification_token, read_verification_token


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        # "Remember me": keep session for SESSION_COOKIE_AGE, else expire on
        # browser close.
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)
        response = super().form_valid(form)
        log_activity(self.request.user, "login", "Logged in", self.request)
        return response


class LogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            log_activity(request.user, "logout", "Logged out", request)
        return super().post(request, *args, **kwargs)


class RegisterView(CreateView):
    model = User
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        self._send_verification_email(self.object)
        messages.success(
            self.request,
            "Account created. Check your inbox to verify your email address.",
        )
        return response

    def _send_verification_email(self, user):
        token = make_verification_token(user)
        url = self.request.build_absolute_uri(
            reverse("accounts:verify_email", args=[token])
        )
        body = render_to_string(
            "emails/verify_email.txt", {"user": user, "verify_url": url}
        )
        send_mail("Verify your CRM account", body, None, [user.email])


def verify_email(request, token):
    user_id = read_verification_token(token)
    if user_id is None:
        messages.error(request, "Verification link is invalid or has expired.")
        return redirect("accounts:login")
    user = get_object_or_404(User, pk=user_id)
    if not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
    messages.success(request, "Email verified — you can now sign in.")
    return redirect("accounts:login")


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


class ChangePasswordView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Password changed successfully.")
        return super().form_valid(form)


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "emails/password_reset_email.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

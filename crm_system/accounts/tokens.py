"""Signed, expiring tokens for email verification (no extra DB table needed)."""
from django.core import signing

VERIFY_SALT = "accounts.email-verify"
VERIFY_MAX_AGE = 60 * 60 * 24 * 3  # 3 days


def make_verification_token(user) -> str:
    return signing.dumps({"user_id": user.pk}, salt=VERIFY_SALT)


def read_verification_token(token: str):
    """Returns the user id or None if the token is invalid/expired."""
    try:
        data = signing.loads(token, salt=VERIFY_SALT, max_age=VERIFY_MAX_AGE)
    except signing.BadSignature:
        return None
    return data.get("user_id")

"""File-upload validation: extension whitelist + size limit."""
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_file_extension(value):
    ext = Path(value.name).suffix.lower()
    allowed = settings.ALLOWED_UPLOAD_EXTENSIONS
    if ext not in allowed:
        raise ValidationError(
            f"File type '{ext}' is not allowed. Allowed: {', '.join(allowed)}"
        )


def validate_file_size(value):
    limit = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if value.size > limit:
        raise ValidationError(
            f"File too large ({value.size // (1024 * 1024)} MB). "
            f"Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB."
        )


FILE_VALIDATORS = [validate_file_extension, validate_file_size]

"""
Tez DEMO sozlamalari — CI/CD ko'rsatish uchun.

PostgreSQL, .env yoki maxfiy kalit TALAB QILMAYDI: ma'lumotlar SQLite faylda.
Faqat namoyish uchun; haqiqiy production ma'lumotlari uchun ishlatmang
(buning uchun config.settings.production bor).
"""
from .base import *  # noqa: F401,F403

# Demo uchun: xatolar ko'rinsin, hamma host ruxsat etilsin (IP orqali kiriladi)
DEBUG = True
ALLOWED_HOSTS = ["*"]

# PostgreSQL o'rniga oddiy SQLite fayl — hech narsa o'rnatish shart emas
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "demo.sqlite3",  # noqa: F405
    }
}

# Static fayllarni oddiy uzatish (manifest/hash yo'q) — collectstatic bo'lmasa ham sahifa buzilmaydi
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}

# Email konsolga chiqadi (SMTP sozlash shart emas)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# --- Cloudflare Tunnel (HTTPS) ---
# Sayt https://...trycloudflare.com orqali ochiladi. Login (POST so'rovi)
# ishlashi uchun bu domen "ishonchli manba" deb belgilanadi (aks holda CSRF 403):
CSRF_TRUSTED_ORIGINS = ["https://*.trycloudflare.com"]
# Cloudflare HTTPS'ni uzatadi; Django so'rovni HTTPS deb tanishi uchun:
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

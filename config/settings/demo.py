"""
DEMO / namoyish sozlamalari — CI/CD ko'rsatish uchun.

Haqiqiy PostgreSQL bazasiga (.env dagi crm_db) ulanadi, lekin Cloudflare tunnel
orqali HTTPS bilan ochilishi uchun moslangan (ALLOWED_HOSTS, CSRF, HTTPS).
DEBUG yoqilgan — namoyish uchun qulay; keyinroq production.py ga o'tish mumkin.
"""
from .base import *  # noqa: F401,F403

import os

# Ommaviy murojaat (contact) formasi maxfiy kalitsiz ishlashi uchun:
# agar serverda CONTACT_API_KEY o'rnatilgan bo'lsa, jarayon muhitidan olib tashlaymiz,
# aks holda forma "403 Forbidden" qaytaradi.
os.environ.pop("CONTACT_API_KEY", None)

# Demo uchun: xatolar ko'rinsin, hamma host ruxsat etilsin (IP orqali kiriladi)
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Ma'lumotlar bazasi: base.py allaqachon .env dagi PostgreSQL (crm_db) ga ulanadi.
# Shuning uchun bu yerda DB ni override QILMAYMIZ — haqiqiy foydalanuvchilar va
# ma'lumotlar (to'g'ri rollari bilan) serverdagi Postgres'dan keladi.

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

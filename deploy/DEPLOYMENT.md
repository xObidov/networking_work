# Deployment Guide — Arch Linux + PostgreSQL + Nginx + Gunicorn

No Docker, no Redis, no Celery — a plain Linux host runs everything.

## 1. System packages

```bash
sudo pacman -Syu
sudo pacman -S python python-pip postgresql nginx git
```

## 2. PostgreSQL

```bash
# First-time cluster init (Arch)
sudo -u postgres initdb -D /var/lib/postgres/data
sudo systemctl enable --now postgresql

sudo -u postgres psql <<'SQL'
CREATE ROLE crm_user WITH LOGIN PASSWORD 'CHANGE-ME-strong-password';
CREATE DATABASE crm_db OWNER crm_user;
SQL
```

## 3. Application user & code

```bash
sudo useradd -r -m -d /srv/crm_system -s /usr/bin/nologin crm
sudo -u crm git clone https://github.com/xObidov/networking_work.git /srv/crm_system
cd /srv/crm_system
sudo -u crm python -m venv .venv
sudo -u crm .venv/bin/pip install -r requirements.txt
```

## 4. Environment variables

```bash
sudo -u crm cp .env.example .env
sudo -u crm nano .env          # fill in SECRET_KEY, DB password, hosts, SMTP
sudo chmod 600 .env            # secrets readable only by the crm user
```

Generate a secret key:

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 5. Migrate, collect static, create admin

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
sudo -u crm -E .venv/bin/python manage.py migrate
sudo -u crm -E .venv/bin/python manage.py collectstatic --noinput
sudo -u crm -E .venv/bin/python manage.py createsuperuser
```

## 6. Gunicorn (systemd)

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/crm-gunicorn.service
sudo systemctl daemon-reload
sudo systemctl enable --now crm-gunicorn
systemctl status crm-gunicorn
```

## 7. Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/conf.d/crm.conf
sudo nano /etc/nginx/conf.d/crm.conf   # replace yourdomain.com
sudo nginx -t && sudo systemctl enable --now nginx
```

For HTTPS, issue a certificate with certbot:

```bash
sudo pacman -S certbot certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 8. Security checklist

- `DEBUG = False` in production (already enforced by `config.settings.production`).
- `.env` is mode 600 and never committed.
- HTTPS-only: SSL redirect, HSTS, secure cookies — all enabled in production settings.
- PostgreSQL listens on localhost only (default).
- File uploads validated by extension + size; Nginx caps body size at 12 MB.
- Keep packages updated: `sudo pacman -Syu` and `pip list --outdated`.

## 9. Updating a running deployment

```bash
cd /srv/crm_system
sudo -u crm git pull
sudo -u crm .venv/bin/pip install -r requirements.txt
sudo -u crm -E .venv/bin/python manage.py migrate
sudo -u crm -E .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart crm-gunicorn
```

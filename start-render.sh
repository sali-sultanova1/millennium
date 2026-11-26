#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
    python manage.py shell <<'PY'
import os

from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]

if not User.objects.filter(username=username).exists():
    call_command("createsuperuser", interactive=False)
PY
fi

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 1
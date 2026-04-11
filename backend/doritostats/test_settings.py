"""
Test-only Django settings.

Inherits all production settings and overrides the database to in-memory
SQLite so test runs never touch the live PostgreSQL instance.
"""

from .settings import *  # noqa: F401, F403

# Use in-memory email backend so no real emails are sent during tests.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Strip email-alerting middleware so tests never make Resend API calls.
MIDDLEWARE = [
    m
    for m in MIDDLEWARE  # noqa: F405
    if m
    not in {
        "backend.fantasy_stats.errors.error_middleware.SecurityAlertMiddleware",
        "backend.fantasy_stats.errors.error_middleware.ErrorStatusEmailMiddleware",
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "OPTIONS": {},
        "TIME_ZONE": None,
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "TEST": {},
    }
}

"""
conftest.py for Django tests in backend/tests/

Overrides the database to use an in-memory SQLite DB so that:
  - No Neon/PostgreSQL connection is required
  - Tests run fast and are fully isolated
  - The migration conflict in playoff_pool is bypassed via --no-migrations

Usage:
    pytest backend/tests/test_auth.py -v --no-migrations
"""

import django
from django.test.utils import override_settings


def pytest_configure(config):
    """Override the database to SQLite before Django sets up."""
    from django.conf import settings

    # Only apply if Django settings are already configured (pytest-django loads them first)
    try:
        _ = settings.DATABASES
    except Exception:
        return

    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }

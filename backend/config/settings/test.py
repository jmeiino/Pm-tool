"""Test settings — uses SQLite for fast, isolated tests."""

from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable Celery in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Silence logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"]},
}

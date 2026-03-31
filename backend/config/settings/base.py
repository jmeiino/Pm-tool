"""
Django base settings for PM-Tool.
"""

from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-secret-key-change-in-production")

DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "django_celery_beat",
]

LOCAL_APPS = [
    "apps.core",
    "apps.users",
    "apps.projects",
    "apps.todos",
    "apps.integrations",
    "apps.ai",
    "apps.notifications",
    "apps.agents",
    "apps.admin_portal",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.AutoAuthMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.kpi_middleware.KPITrackingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Cache (Redis)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://redis:6379/1"),
        "TIMEOUT": 300,  # 5 Minuten Standard-TTL
    }
}

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="pmtool"),
        "USER": config("POSTGRES_USER", default="pmtool"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="pmtool"),
        "HOST": config("POSTGRES_HOST", default="db"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

# Custom User Model
AUTH_USER_MODEL = "users.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# DRF Spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    "TITLE": "PM-Tool API",
    "DESCRIPTION": "Persönliches Projektmanagement Tool API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# JWT
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3115",
    cast=Csv(),
)

# Celery
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    "check-deadline-warnings": {
        "task": "apps.notifications.tasks.check_deadline_warnings",
        "schedule": 3600.0,  # every hour
    },
}

# External Services
ATLASSIAN_URL = config("ATLASSIAN_URL", default="")
ATLASSIAN_EMAIL = config("ATLASSIAN_EMAIL", default="")
ATLASSIAN_API_TOKEN = config("ATLASSIAN_API_TOKEN", default="")

MS_CLIENT_ID = config("MS_CLIENT_ID", default="")
MS_CLIENT_SECRET = config("MS_CLIENT_SECRET", default="")
MS_TENANT_ID = config("MS_TENANT_ID", default="")
MS_REDIRECT_URI = config("MS_REDIRECT_URI", default="http://localhost:4107/api/v1/integrations/microsoft/callback/")

GITHUB_TOKEN = config("GITHUB_TOKEN", default="")

# AI Provider: "claude", "ollama" oder "openrouter"
AI_PROVIDER = config("AI_PROVIDER", default="claude")

ANTHROPIC_API_KEY = config("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = config("ANTHROPIC_MODEL", default="claude-sonnet-4-20250514")

# Ollama (lokal)
OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="http://localhost:11434")
OLLAMA_MODEL = config("OLLAMA_MODEL", default="llama3.1")

# OpenRouter
OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")
OPENROUTER_MODEL = config("OPENROUTER_MODEL", default="anthropic/claude-sonnet-4")
OPENROUTER_REFERER = config("OPENROUTER_REFERER", default="http://localhost:4107")

# KPI-Tracking
KPI_API_URL = config("KPI_API_URL", default="")
KPI_TRACKING_URL = config("KPI_TRACKING_URL", default="") or KPI_API_URL
KPI_API_KEY = config("KPI_API_KEY", default="")

# PM-Tool Base URL (fuer Paperclip callback_url Konstruktion)
PM_TOOL_BASE_URL = config("PM_TOOL_BASE_URL", default="http://localhost:4107")

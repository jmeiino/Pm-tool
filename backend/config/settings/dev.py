"""Development settings."""

from .base import *  # noqa: F401, F403

DEBUG = True

# In development, also render browsable API and allow AutoAuth as fallback
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
    "rest_framework_simplejwt.authentication.JWTAuthentication",
    "apps.core.middleware.AutoAuthDRF",
]

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["http://localhost:3115"]

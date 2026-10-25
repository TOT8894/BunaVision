"""All configuration comes from environment variables. Required ones have no default and stop the
process at startup with a message naming the variable."""

import math
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
APP_VERSION = "0.5.0"


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} is required but not set")
    return value


def _str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _number(name: str, default: float, cast=int, *, minimum: float = 0):  # noqa: ANN001, ANN202
    raw = os.environ.get(name)
    if raw is None:
        return cast(default)
    try:
        value = cast(raw)
    except ValueError:
        raise ImproperlyConfigured(f"{name} must be a valid number") from None
    if not math.isfinite(value) or value < minimum:
        raise ImproperlyConfigured(f"{name} must be finite and at least {minimum}")
    return value


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean (true/false, yes/no, on/off, or 1/0)")


def _csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Core Django ---------------------------------------------------------------------------
SECRET_KEY = _required("SECRET_KEY")
DEBUG = _bool("DEBUG", False)
ALLOWED_HOSTS = _csv(_required("ALLOWED_HOSTS"))
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must contain at least one hostname")
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
APPEND_SLASH = False  # the API paths have no trailing slash
AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TIME_ZONE = "UTC"
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "apps.accounts",
    "apps.assessments",
]

MIDDLEWARE = [
    "apps.common.middleware.RequestIdMiddleware",
    "apps.common.middleware.BodySizeLimitMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves the Django admin's static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# --- Database and cache --------------------------------------------------------------------
DATABASES = {"default": dj_database_url.parse(_required("DATABASE_URL"))}
DATABASES["default"].update(CONN_MAX_AGE=60, CONN_HEALTH_CHECKS=True, ATOMIC_REQUESTS=False)
# Never hold a transaction open while calling vision or Gemini: only the final insert is atomic.

# Throttle counters must be shared by all workers, so not the default per-process memory cache.
if os.environ.get("REDIS_URL"):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": os.environ["REDIS_URL"]}}
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "django_cache"}}
    # run once: python manage.py createcachetable

# --- Auth ----------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
ACCESS_TOKEN_TTL_S = _number("ACCESS_TOKEN_TTL_S", 3600)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=ACCESS_TOKEN_TTL_S),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
MAX_ASSESSMENTS_PER_USER_PER_HOUR = _number("MAX_ASSESSMENTS_PER_USER_PER_HOUR", 30, minimum=1)
# Per process x threads: size gunicorn (--workers x --threads) to this; it replaces a semaphore.
MAX_CONCURRENT_ASSESSMENTS = _number("WEB_CONCURRENCY", 2, minimum=1) * _number("GUNICORN_THREADS", 4, minimum=1)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.handler.exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "assessments": f"{MAX_ASSESSMENTS_PER_USER_PER_HOUR}/hour",
        "auth": "10/min",
    },
    # 0 = trust REMOTE_ADDR only. Behind a proxy set NUM_PROXIES to the number of proxies,
    # otherwise every client shares the proxy's address (or, if unset, X-Forwarded-For is spoofable).
    "NUM_PROXIES": _number("NUM_PROXIES", 0, minimum=0),
}
SPECTACULAR_SETTINGS = {
    "TITLE": "BunaVision API",
    "DESCRIPTION": "Preliminary AI screening of green coffee sample photos. Results are model predictions, not official grades.",
    "VERSION": APP_VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- CORS ----------------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = _csv(_str("CORS_ALLOWED_ORIGINS", ""))
if "*" in CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must list real origins, not '*'")
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
CORS_ALLOW_HEADERS = ["authorization", "content-type", "idempotency-key", "x-request-id"]
CORS_EXPOSE_HEADERS = ["X-Request-ID"]
CORS_ALLOW_CREDENTIALS = False  # tokens travel in the Authorization header, not cookies

# --- Images and external services ----------------------------------------------------------
MAX_IMAGE_BYTES = _number("MAX_IMAGE_BYTES", 10 * 1024 * 1024, minimum=1)
MAX_IMAGE_PIXELS = _number("MAX_IMAGE_PIXELS", 50_000_000, minimum=1)
MIN_IMAGE_SIDE_PX = _number("MIN_IMAGE_SIDE_PX", 320, minimum=1)  # provisional: confirm against the vision model
RETAIN_ORIGINAL_IMAGE = _bool("RETAIN_ORIGINAL_IMAGE", True)
IMAGE_URL_TTL_S = _number("IMAGE_URL_TTL_S", 900, minimum=1)

VISION_SERVICE_URL = _required("VISION_SERVICE_URL")
VISION_TIMEOUT_S = _number("VISION_TIMEOUT_S", 30, float, minimum=0.001)
VISION_CONNECT_TIMEOUT_S = _number("VISION_CONNECT_TIMEOUT_S", 3, float, minimum=0.001)
VISION_RELOAD_TIMEOUT_S = _number("VISION_RELOAD_TIMEOUT_S", 60, float, minimum=0.001)

GEMINI_API_KEY = _required("GEMINI_API_KEY")
GEMINI_MODEL = _required("GEMINI_MODEL")  # check Google's deprecations page: models are retired
GEMINI_TIMEOUT_S = _number("GEMINI_TIMEOUT_S", 30, float, minimum=0.001)
GEMINI_TEMPERATURE = _number("GEMINI_TEMPERATURE", 0.2, float, minimum=0)
GEMINI_MAX_OUTPUT_TOKENS = _number("GEMINI_MAX_OUTPUT_TOKENS", 8192, minimum=1)

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"}}

IMAGE_STORE = _required("IMAGE_STORE")
if IMAGE_STORE == "s3":
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": _required("S3_BUCKET"),
            "region_name": _required("S3_REGION"),
            "endpoint_url": os.environ.get("S3_ENDPOINT_URL") or None,  # MinIO and friends
            "querystring_auth": True,  # private bucket + short-lived signed URLs
            "querystring_expire": IMAGE_URL_TTL_S,
            "default_acl": None,
            "file_overwrite": False,
            "signature_version": "s3v4",
        },
    }
elif IMAGE_STORE == "memory":
    # Development only: images vanish on restart and the URLs are not fetchable.
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
        "OPTIONS": {"base_url": "http://memory.invalid/images/"},
    }
else:
    raise ImproperlyConfigured(f"IMAGE_STORE must be 'memory' or 's3', got {IMAGE_STORE!r}")

# --- Security and logging ------------------------------------------------------------------
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = not DEBUG
LOG_LEVEL = _str("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "apps.common.logging.RequestIdFilter"}},
    "formatters": {"std": {"format": "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "filters": ["request_id"], "formatter": "std"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

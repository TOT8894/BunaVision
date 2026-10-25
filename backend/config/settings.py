"""All configuration comes from environment variables or .env file via python-decouple.
Required settings have no default and fail fast at startup naming the missing variable."""

from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
APP_VERSION = "0.5.0"


# --- Core Django ---------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
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
DATABASES = {"default": dj_database_url.parse(config("DATABASE_URL"))}
DATABASES["default"].update(CONN_MAX_AGE=60, CONN_HEALTH_CHECKS=True, ATOMIC_REQUESTS=False)
# Never hold a transaction open while calling vision or Gemini: only the final insert is atomic.

# Throttle counters must be shared by all workers, so not the default per-process memory cache.
REDIS_URL = config("REDIS_URL", default=None)
if REDIS_URL:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}}
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "django_cache"}}
    # run once: python manage.py createcachetable

# --- Auth ----------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
ACCESS_TOKEN_TTL_S = config("ACCESS_TOKEN_TTL_S", default=3600, cast=int)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=ACCESS_TOKEN_TTL_S),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
MAX_ASSESSMENTS_PER_USER_PER_HOUR = config("MAX_ASSESSMENTS_PER_USER_PER_HOUR", default=30, cast=int)
# Per process x threads: size gunicorn (--workers x --threads) to this; it replaces a semaphore.
MAX_CONCURRENT_ASSESSMENTS = config("WEB_CONCURRENCY", default=2, cast=int) * config("GUNICORN_THREADS", default=4, cast=int)

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
    "NUM_PROXIES": config("NUM_PROXIES", default=0, cast=int),
}
SPECTACULAR_SETTINGS = {
    "TITLE": "BunaVision API",
    "DESCRIPTION": "Preliminary AI screening of green coffee sample photos. Results are model predictions, not official grades.",
    "VERSION": APP_VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- CORS ----------------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())
if "*" in CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must list real origins, not '*'")
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
CORS_ALLOW_HEADERS = ["authorization", "content-type", "idempotency-key", "x-request-id"]
CORS_EXPOSE_HEADERS = ["X-Request-ID"]
CORS_ALLOW_CREDENTIALS = False  # tokens travel in the Authorization header, not cookies

# --- Images and external services ----------------------------------------------------------
MAX_IMAGE_BYTES = config("MAX_IMAGE_BYTES", default=10 * 1024 * 1024, cast=int)
MAX_IMAGE_PIXELS = config("MAX_IMAGE_PIXELS", default=50_000_000, cast=int)
MIN_IMAGE_SIDE_PX = config("MIN_IMAGE_SIDE_PX", default=320, cast=int)  # provisional: confirm against the vision model
RETAIN_ORIGINAL_IMAGE = config("RETAIN_ORIGINAL_IMAGE", default=True, cast=bool)
IMAGE_URL_TTL_S = config("IMAGE_URL_TTL_S", default=900, cast=int)

VISION_SERVICE_URL = config("VISION_SERVICE_URL")
VISION_TIMEOUT_S = config("VISION_TIMEOUT_S", default=30.0, cast=float)
VISION_CONNECT_TIMEOUT_S = config("VISION_CONNECT_TIMEOUT_S", default=3.0, cast=float)
VISION_RELOAD_TIMEOUT_S = config("VISION_RELOAD_TIMEOUT_S", default=60.0, cast=float)

GEMINI_API_KEY = config("GEMINI_API_KEY")
GEMINI_MODEL = config("GEMINI_MODEL")  # check Google's deprecations page: models are retired
GEMINI_TIMEOUT_S = config("GEMINI_TIMEOUT_S", default=30.0, cast=float)
GEMINI_TEMPERATURE = config("GEMINI_TEMPERATURE", default=0.2, cast=float)
GEMINI_MAX_OUTPUT_TOKENS = config("GEMINI_MAX_OUTPUT_TOKENS", default=8192, cast=int)

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"}}

IMAGE_STORE = config("IMAGE_STORE")
if IMAGE_STORE == "s3":
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": config("S3_BUCKET"),
            "region_name": config("S3_REGION"),
            "endpoint_url": config("S3_ENDPOINT_URL", default=None),  # MinIO and friends
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
LOG_LEVEL = config("LOG_LEVEL", default="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "apps.common.logging.RequestIdFilter"}},
    "formatters": {"std": {"format": "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "filters": ["request_id"], "formatter": "std"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

from pathlib import Path
import os
import sys

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_csv(name: str, default_csv: str = "") -> list[str]:
    raw = os.environ.get(name, default_csv)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


SECRET_KEY = _env("SECRET_KEY", _env("DJANGO_SECRET_KEY", "change-me"))
DEBUG = _env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = _env_csv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.onrender.com")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "library",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "steamlike_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "steamlike_backend.wsgi.application"

DATABASE_URL = _env("DATABASE_URL")

if "test" in sys.argv:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
elif DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _env("POSTGRES_DB", "steamlike"),
            "USER": _env("POSTGRES_USER", "steamlike"),
            "PASSWORD": _env("POSTGRES_PASSWORD", "steamlike"),
            "HOST": _env("POSTGRES_HOST", "db"),
            "PORT": _env("POSTGRES_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
WHITENOISE_USE_FINDERS = _env_bool("WHITENOISE_USE_FINDERS", True)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = _env_csv(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    "http://frontend:3000,http://localhost:3000,https://steamlike-backend-1.onrender.com",
)
CORS_ALLOWED_ORIGIN_REGEXES = _env_csv(
    "DJANGO_CORS_ALLOWED_ORIGIN_REGEXES",
    r"^https://.*\.onrender\.com$",
)
CORS_ALLOW_CREDENTIALS = _env_bool("DJANGO_CORS_ALLOW_CREDENTIALS", True)

CSRF_TRUSTED_ORIGINS = _env_csv(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://frontend:3000,http://localhost:3000,https://*.onrender.com",
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = _env_bool("DJANGO_SESSION_COOKIE_SECURE", False)
CSRF_COOKIE_SECURE = _env_bool("DJANGO_CSRF_COOKIE_SECURE", False)

MAILEROO_API_URL = _env("MAILEROO_API_URL", "https://smtp.maileroo.com/api/v2/emails")
MAILEROO_API_KEY = _env("MAILEROO_API_KEY", "")
MAILEROO_FROM_ADDRESS = _env("MAILEROO_FROM_ADDRESS", "")
MAILEROO_FROM_NAME = _env("MAILEROO_FROM_NAME", "Nexus Play")
MAILEROO_TIMEOUT = _env_float("MAILEROO_TIMEOUT", 5.0)

CHEAPSHARK_API_URL = _env("CHEAPSHARK_API_URL", "https://www.cheapshark.com/api/1.0/games")
CHEAPSHARK_TIMEOUT = _env_float("CHEAPSHARK_TIMEOUT", 5.0)
REDIS_URL = _env("REDIS_URL", "redis://localhost:6379/0")
CATALOG_SEARCH_CACHE_TTL_SECONDS = _env_int("CATALOG_SEARCH_CACHE_TTL_SECONDS", 300)
CATALOG_SEARCH_STALE_CACHE_TTL_SECONDS = _env_int(
    "CATALOG_SEARCH_STALE_CACHE_TTL_SECONDS",
    86400,
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "library.email_service": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "library.catalog_service": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

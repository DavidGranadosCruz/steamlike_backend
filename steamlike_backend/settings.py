from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)

def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

def _env_csv(name: str, default_csv: str = "") -> list[str]:
    raw = os.environ.get(name, default_csv)
    items = [x.strip() for x in raw.split(",") if x.strip()]
    return items

SECRET_KEY = _env("DJANGO_SECRET_KEY", "change-me")
DEBUG = _env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = _env_csv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party.
    "corsheaders",

    # Local apps
    "library",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",
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

WSGI_APPLICATION = "steamlike_backend.wsgi.application"

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

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS + cookies (SessionAuthentication) ---
CORS_ALLOWED_ORIGINS = _env_csv("DJANGO_CORS_ALLOWED_ORIGINS", "http://frontend:3000,http://localhost:3000")
CORS_ALLOW_CREDENTIALS = _env_bool("DJANGO_CORS_ALLOW_CREDENTIALS", True)

CSRF_TRUSTED_ORIGINS = _env_csv("DJANGO_CSRF_TRUSTED_ORIGINS", "http://frontend:3000,http://localhost:3000")

# Dev defaults for cookies (keep simple; hardening can be done later)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return str(env(name, str(default))).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    return int(env(name, default))


DEBUG = env_bool("DJANGO_DEBUG", False)


def _secret(name, dev_default):
    value = env(name)
    if value:
        return value
    if DEBUG:
        return dev_default
    raise RuntimeError(f"{name} must be set when DJANGO_DEBUG is false")


SECRET_KEY = _secret("DJANGO_SECRET_KEY", "dev-only-insecure-key")
QR_SIGNING_SECRET = _secret("QR_SIGNING_SECRET", "dev-only-qr-secret")
PSEUDONYM_SECRET = _secret("PSEUDONYM_SECRET", "dev-only-pseudonym-secret")
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]

USE_P1_STUB = env_bool("USE_P1_STUB", True)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.common",
    "apps.qr_validation",
    "apps.voter_authorization",
    "apps.anonymous_authorization",
    "apps.duplicate_voting",
    "apps.ballot_management",
    "apps.vote_submission",
    "apps.vote_encryption",
    "apps.nizk_proofs",
    "apps.anonymous_storage",
    "apps.authorization_management",
    "apps.audit_management",
    "apps.election_verification",
    "apps.result_calculation",
    "apps.result_publication",
    "apps.ai_assistance",
]
if USE_P1_STUB:
    INSTALLED_APPS.insert(6, "apps.p1_stub")  # local stand-in for Person 1's tables

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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
            ]
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "evoting"),
        "USER": env("DB_USER", "evoting"),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_CONTENT_TYPE_NOSNIFF = True

# ---------------------------------------------------------------- DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",  # Postman-friendly; HTTPS only!
    ],
    # Deny by default: public endpoints must opt in with AllowAny (see apps.common.views).
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAdminUser"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"user": "600/min", "public": "120/min", "submit": "30/min"},
}

# ---------------------------------------------------------------- Person 1 integration
P1_VOTER_MODEL = env("P1_VOTER_MODEL", "p1_stub.Voter")
P1_ELECTION_MODEL = env("P1_ELECTION_MODEL", "p1_stub.Election")
P1_CANDIDATE_MODEL = env("P1_CANDIDATE_MODEL", "p1_stub.Candidate")
# Map our logical names to Person 1's real column names once they confirm them.
P1_FIELDS = {
    "voter_active": "is_active",
    "election_status": "status",
    "candidate_election": "election",
    "candidate_active": "is_active",   # set to None if candidates have no such flag
    "candidate_label": "name",
}
# Map election phases to the status values Person 1 stores.
P1_STATUS_VALUES = {"registration": "upcoming", "voting": "ongoing", "closed": "closed"}

# ---------------------------------------------------------------- e-voting settings
QR_TOKEN_TTL_SECONDS = env_int("QR_TOKEN_TTL_SECONDS", 15 * 60)
PAILLIER_KEY_BITS = env_int("PAILLIER_KEY_BITS", 2048)
KEY_STORE_DIR = Path(env("KEY_STORE_DIR", BASE_DIR / "secure_keys"))
ELECTION_KEY_PASSPHRASE = env("ELECTION_KEY_PASSPHRASE", "")
MIN_RING_SIZE = env_int("MIN_RING_SIZE", 3)
ENABLE_DEMO_ENDPOINTS = env_bool("ENABLE_DEMO_ENDPOINTS", DEBUG)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

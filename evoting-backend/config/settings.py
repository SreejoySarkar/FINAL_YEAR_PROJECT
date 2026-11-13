import sys
from datetime import timedelta
from pathlib import Path

from corsheaders.defaults import default_headers
from decouple import Csv, config
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default=None) or config("DJANGO_SECRET_KEY")
DEBUG = config(
    "DEBUG",
    default=config("DJANGO_DEBUG", default=False),
    cast=bool,
)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default=config(
        "DJANGO_ALLOWED_HOSTS",
        default="localhost,127.0.0.1",
    ),
    cast=Csv(),
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party applications
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "corsheaders",

    # Our project applications
    "accounts",
    "elections",
    "voters",
    "qrtokens",
    "audit",
    "voting",
    "results",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.security_headers.SecurityHeadersMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "django.template.context_processors.csp",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

TESTING = "pytest" in sys.modules or "test" in sys.argv

db_name = config("DB_NAME", default=None)

if db_name:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432"),
            "TEST": {
                "NAME": f"test_{db_name}",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Use the project's custom user model instead of Django's built-in auth.User.
AUTH_USER_MODEL = "accounts.Admin"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_ALLOW_ALL_ORIGINS = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle"
    ],
    "DEFAULT_THROTTLE_RATES": {
    "anon": "30/min",
    "vote": config("VOTE_THROTTLE", default="120/min"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=8),
}

ADMIN_OTP_SALT = config("ADMIN_OTP_SALT", default="admin-otp-session")
ADMIN_OTP_VALID_MINUTES = config(
    "ADMIN_OTP_VALID_MINUTES",
    default=5,
    cast=int,
)
ADMIN_OTP_MAX_ATTEMPTS = config(
    "ADMIN_OTP_MAX_ATTEMPTS",
    default=5,
    cast=int,
)

SPECTACULAR_SETTINGS = {
    "TITLE": "Secure E-Voting API",
    "DESCRIPTION": "Backend APIs (Person 1: management, Person 2: voting)",
    "VERSION": "1.0.0",
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:5173",
    cast=Csv(),
)
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-vote-session",
]
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="",
    cast=Csv(),
)

CSRF_COOKIE_HTTPONLY = True

QR_SIGNING_KEY = config("QR_SIGNING_KEY", default=None) or config(
    "QR_SIGNING_SECRET"
)
QR_TOKEN_SALT = config("QR_TOKEN_SALT", default="evoting-qr-token")

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

MAILER_BACKEND = config(
    "MAILER_BACKEND",
    default=(
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)
EMAIL_OPTIONS = {}
if MAILER_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    EMAIL_OPTIONS = {
        "host": config("EMAIL_HOST", default="localhost"),
        "port": config("EMAIL_PORT", default=25, cast=int),
        "username": config("EMAIL_HOST_USER", default=""),
        "password": config("EMAIL_HOST_PASSWORD", default=""),
        "use_tls": config("EMAIL_USE_TLS", default=False, cast=bool),
        "use_ssl": config("EMAIL_USE_SSL", default=False, cast=bool),
        "timeout": config("EMAIL_TIMEOUT", default=10, cast=int),
    }

MAILERS = {
    "default": {
        "BACKEND": MAILER_BACKEND,
        "OPTIONS": EMAIL_OPTIONS,
    },
}
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="noreply@evoting.local",
)

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_RESOURCE_POLICY = "same-origin"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF, CSP.NONCE],
    "img-src": [CSP.SELF, "data:"],
    "font-src": [CSP.SELF, "data:"],
    "connect-src": [CSP.SELF],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
}
SECURE_SSL_REDIRECT = config(
    "SECURE_SSL_REDIRECT",
    default=not DEBUG,
    cast=bool,
)
SECURE_HSTS_SECONDS = config(
    "SECURE_HSTS_SECONDS",
    default=0,
    cast=int,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
    cast=bool,
)
SECURE_HSTS_PRELOAD = config(
    "SECURE_HSTS_PRELOAD",
    default=False,
    cast=bool,
)
SESSION_COOKIE_SECURE = config(
    "SESSION_COOKIE_SECURE",
    default=not DEBUG,
    cast=bool,
)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SECURE = config(
    "CSRF_COOKIE_SECURE",
    default=not DEBUG,
    cast=bool,
)
CSRF_COOKIE_SAMESITE = "Strict"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SERVER_SOFTWARE_HEADER = ""
BALLOT_MASTER_KEY = config("BALLOT_MASTER_KEY")
INTEGRITY_KEY = config("INTEGRITY_KEY")

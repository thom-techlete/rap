"""
Security settings for the rap_web Django project.
This file contains all security-related configurations separated from the main settings.
"""

from decouple import config

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

# HTTPS settings (for production)
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SECURE_HSTS_SECONDS = config(
    "SECURE_HSTS_SECONDS", default=31536000, cast=int
)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool
)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)

# Cookie security
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "rap_sessionid"
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_NAME = "rap_csrftoken"

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Temporary for inline scripts
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # For inline styles
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
    "https://fonts.googleapis.com",
)
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",
    "https://cdnjs.cloudflare.com",
)
CSP_IMG_SRC = (
    "'self'",
    "data:",  # For inline images
    "blob:",  # For blob URLs
)
CSP_CONNECT_SRC = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# =============================================================================
# AUTHENTICATION SECURITY
# =============================================================================

# Enhanced password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {
            "user_attributes": ("username", "email", "first_name", "last_name"),
            "max_similarity": 0.7,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,  # Increased from default 8
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Account lockout configuration (django-axes)
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5  # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 1  # 1 hour lockout
AXES_RESET_ON_SUCCESS = True
# In production with load balancer, lock by username only (not IP)
# because all requests appear to come from the same IP (load balancer)
AXES_LOCK_OUT_BY_USER_OR_IP = False
AXES_ENABLE_ADMIN = False  # Don't lock out admin
AXES_ONLY_USER_FAILURES = True
AXES_HANDLER = "axes.handlers.database.AxesDatabaseHandler"
# Use X-Forwarded-For header for IP detection when behind proxy
AXES_PROXY_COUNT = 1

# Session security
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_SAVE_EVERY_REQUEST = True

# =============================================================================
# RATE LIMITING
# =============================================================================

# Rate limiting configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"

# =============================================================================
# FILE UPLOAD SECURITY
# =============================================================================

# File upload restrictions
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Allowed file extensions for uploads
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# =============================================================================
# LOGGING SECURITY
# =============================================================================

# Security logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "security": {
            "format": "{levelname} {asctime} {name} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "verbose": {
            "format": "{levelname} {asctime} {name} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/tmp/rap_security.log",
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "backupCount": 5,
            "formatter": "security",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.security": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "axes": {
            "handlers": ["security_file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "rap_web.security": {
            "handlers": ["security_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# =============================================================================
# ADMIN SECURITY
# =============================================================================

# Admin interface security
ADMIN_URL = config("ADMIN_URL", default="admin/")

# =============================================================================
# DATABASE SECURITY
# =============================================================================

# Database connection security
DATABASES_DEFAULT_OPTIONS = {
    "sslmode": config("DB_SSLMODE", default="prefer"),
    "options": {
        "application_name": "rap_web",
    },
}

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

# CORS settings (if API endpoints are needed)
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Never allow all origins in production

# =============================================================================
# SECURITY MIDDLEWARE ORDER
# =============================================================================

SECURITY_MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Static files security
    "axes.middleware.AxesMiddleware",  # Account lockout
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS
    "csp.middleware.CSPMiddleware",  # Content Security Policy
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",  # Rate limiting
    "rap_web.middleware.LoginRequiredMiddleware",  # Custom auth middleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =============================================================================
# DEVELOPMENT OVERRIDES
# =============================================================================


def apply_development_security_settings(settings_dict):
    """
    Apply less strict security settings for development.
    This function should only be called in development environments.
    """
    if config("DJANGO_DEBUG", default=True, cast=bool):
        # Relaxed CSP for development
        settings_dict.update(
            {
                "CSP_SCRIPT_SRC": (
                    "'self'",
                    "'unsafe-inline'",
                    "'unsafe-eval'",  # For development tools
                    "https://cdn.jsdelivr.net",
                    "https://cdnjs.cloudflare.com",
                ),
                "CSP_STYLE_SRC": (
                    "'self'",
                    "'unsafe-inline'",
                    "https://cdn.jsdelivr.net",
                    "https://cdnjs.cloudflare.com",
                    "https://fonts.googleapis.com",
                ),
                # Disable HTTPS redirects in development
                "SECURE_SSL_REDIRECT": False,
                "SESSION_COOKIE_SECURE": False,
                "CSRF_COOKIE_SECURE": False,
                # Relaxed rate limiting
                "AXES_FAILURE_LIMIT": 10,
                "AXES_COOLOFF_TIME": 0.1,  # 6 minutes
            }
        )

    return settings_dict

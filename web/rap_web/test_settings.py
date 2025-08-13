from .settings import *

# Override database settings for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.db",
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

# MIGRATION_MODULES = DisableMigrations()

# Simplify password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
LOGGING_CONFIG = None

# Disable CSRF during testing
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
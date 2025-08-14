"""
Local development settings override
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Override database to use SQLite for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.db",
    }
}

# Enable debug mode
DEBUG = True

# Allow all hosts for development
ALLOWED_HOSTS = ['*']
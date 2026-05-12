# sundowns_app/settings/test.py

from .base import *

DEBUG = False

SECRET_KEY = config(
    "SECRET_KEY",
    default="test-secret-key-for-sundowns-project-at-least-32-chars"
)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="sundowns_db"),
        "USER": config("DB_USER", default="sundowns_user"),
        "PASSWORD": config("DB_PASSWORD", default="sundowns_password"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
        "TEST": {
            "NAME": config("TEST_DB_NAME", default="test_sundowns_db"),
        },
    }
}

MEDIA_ROOT = BASE_DIR / "test_media"

STATIC_ROOT = BASE_DIR / "test_staticfiles"
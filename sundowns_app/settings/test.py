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
        "ENGINE": config("TEST_DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("TEST_DB_NAME", default=str(BASE_DIR / "test_db.sqlite3")),
        "USER": config("DB_USER", default=""),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default=""),
        "PORT": config("DB_PORT", default=""),
        "TEST": {
            "NAME": config("TEST_DB_NAME", default=str(BASE_DIR / "test_db.sqlite3")),
        },
    }
}

MEDIA_ROOT = BASE_DIR / "test_media"

STATIC_ROOT = BASE_DIR / "test_staticfiles"
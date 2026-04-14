# sundowns_app/settings/prod.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sundowns_prod',
        'USER': 'postgres',
        'PASSWORD': 'securepassword',
        'HOST': 'prod-db-host',   # e.g. RDS, managed DB
        'PORT': '5432',
    }
}

# Static & media files served via CDN or cloud storage
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/sundowns/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/sundowns/media/'

# Production logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/sundowns/django_errors.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR',
    },
}

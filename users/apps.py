"""Users app configuration for the Sundowns project.

This module declares the Django application configuration for the users
application, including model primary key defaults.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Users application configuration.

    Registers the users app with Django and enforces a consistent default
    primary key field type for models in the users package.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

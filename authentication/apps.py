"""Authentication app configuration for the Sundowns project.

This module defines the application configuration class used by Django to
register and configure the authentication application within the project.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Authentication application configuration.

    This class registers the authentication app with Django and defines the
    default primary key field type for any models declared in this app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'

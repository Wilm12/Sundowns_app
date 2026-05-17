"""Common app configuration for the Sundowns project.

This module defines the Django application configuration for shared utilities and
common functionality used by multiple apps.
"""

from django.apps import AppConfig


class Config(AppConfig):
    """Common application configuration.

    Registers the common app and enforces a consistent default primary key
    field type for models defined in the shared common package.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'


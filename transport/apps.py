"""Transport app configuration for the Sundowns project.

This module defines the Django application configuration for the transport app
and the default behavior for its models.
"""

from django.apps import AppConfig


class Config(AppConfig):
    """Transport application configuration.

    Registers the transport app and establishes a consistent default primary
    key field type for models in the transport package.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transport'


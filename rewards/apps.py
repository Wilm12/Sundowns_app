"""Rewards app configuration for the Sundowns project.

This module defines the Django application configuration for the rewards app
and the default behavior for its models.
"""

from django.apps import AppConfig


class Config(AppConfig):
    """Rewards application configuration.

    Registers the rewards app and sets a consistent default primary key field
    type for models in the rewards package.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rewards'


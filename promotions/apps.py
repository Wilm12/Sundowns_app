"""Promotions app configuration for the Sundowns project.

This module defines the Django application configuration for the promotions app
and its shared model defaults.
"""

from django.apps import AppConfig


class Config(AppConfig):
    """Promotions application configuration.

    Registers the promotions app and ensures a consistent default primary key
    field type for promotional models.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'promotions'


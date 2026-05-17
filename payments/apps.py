"""Payments app configuration for the Sundowns project.

This module defines the Django application configuration for the payments
app and its default model field behavior.
"""

from django.apps import AppConfig


class Config(AppConfig):
    """Payments application configuration.

    Registers the payments app and ensures a consistent primary key field type
    for model definitions within the payments package.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'


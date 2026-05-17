"""Ticketing app configuration for the Sundowns project.

This module defines the Django application configuration for the ticketing app
and its default model primary key behavior.
"""

from django.apps import AppConfig


class Config(AppConfig):
    """Ticketing application configuration.

    Registers the ticketing app and sets the default primary key field type for
    models defined in this app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ticketing'


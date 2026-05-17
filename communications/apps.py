"""Communications app configuration for the Sundowns project.

This module defines the Django application configuration for the communications
app and its model behavior.
"""

from django.apps import AppConfig


class Config(AppConfig):
    """Communications application configuration.

    Registers the communications app and specifies the default primary key
    field behavior for models defined in this app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communications'


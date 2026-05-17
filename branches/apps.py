"""Branches app configuration for the Sundowns project.

This module defines the Django application configuration for the branches app
and its default model behavior.
"""

from django.apps import AppConfig


class BranchesConfig(AppConfig):
    """Branches application configuration.

    Registers the branches app and specifies a standard default primary key
    field type for branch-related models.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'branches'

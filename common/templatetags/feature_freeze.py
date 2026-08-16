"""Template tags for feature freeze state."""

from django import template
from sundowns_app.feature_freeze import is_frozen

register = template.Library()


@register.filter
def frozen(feature_name):
    """Check if a feature is frozen.
    
    Usage: {% if 'supporter'|frozen %}...{% endif %}
    """
    return is_frozen(feature_name)


@register.simple_tag
def is_feature_frozen(feature_name):
    """Check if a feature is frozen (tag version).
    
    Usage: {% is_feature_frozen 'supporter' as supporter_frozen %}
    """
    return is_frozen(feature_name)

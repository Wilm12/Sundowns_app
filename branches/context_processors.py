from django.urls import reverse

from .services.authorization import is_branch_admin
from sundowns_app.feature_freeze import is_frozen


def branch_admin_context(request):
    user = getattr(request, "user", None)
    is_admin = is_branch_admin(user)

    return {
        "is_branch_admin": is_admin,
        "branch_admin_dashboard_url": reverse("branch_admin_dashboard") if is_admin else None,
        # Feature freeze state variables for template use
        "supporter_frozen": is_frozen("supporter"),
        "loyalty_frozen": is_frozen("loyalty"),
        "engagement_frozen": is_frozen("engagement"),
        "transport_frozen": is_frozen("transport"),
    }

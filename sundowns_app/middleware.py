"""
Middleware to enforce feature freeze restrictions.

This middleware prevents authenticated users from reaching frozen feature routes.
It blocks only the explicitly mapped feature prefixes and leaves active areas
and administrative/auth routes untouched.
"""

from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from sundowns_app.feature_freeze import is_frozen


# Map URL prefixes to frozen feature names.
# Keep this list intentionally narrow so active areas like /analytics/,
# /matches/, /tickets/, /payments/, /branch-admin/, /admin/, and API endpoints
# remain available while the frozen supporter/loyalty/engagement/transport domains
# are inaccessible.
FROZEN_ROUTE_MAPPING = {
    "/membership/": "supporter",
    "/branches/": "supporter",
    "/points/": "loyalty",
    "/rewards/": "loyalty",
    "/engagement/": "engagement",
    "/campaigns/": "engagement",
    "/competitions/": "engagement",
    "/transport/": "transport",
}

EXCLUDED_PREFIXES = (
    "/admin/",
    "/api/",
    "/health/",
    "/common/health/",
    "/static/",
    "/media/",
    "/django_prometheus/",
)


class FeatureFreezeMiddleware(MiddlewareMixin):
    """Middleware to block access to frozen features."""

    def process_request(self, request):
        """Check if the request path is for a frozen feature and block if needed."""
        if not getattr(request.user, "is_authenticated", False):
            return None

        path = request.path or "/"

        if any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            return None

        for route_prefix, feature_name in FROZEN_ROUTE_MAPPING.items():
            if path.startswith(route_prefix) and is_frozen(feature_name):
                return render(
                    request,
                    "403.html",
                    {
                        "message": f"This feature is temporarily frozen.",
                        "feature": feature_name,
                    },
                    status=403,
                )

        return None

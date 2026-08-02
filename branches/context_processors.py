from django.urls import reverse

from .services.authorization import is_branch_admin


def branch_admin_context(request):
    user = getattr(request, "user", None)
    is_admin = is_branch_admin(user)

    return {
        "is_branch_admin": is_admin,
        "branch_admin_dashboard_url": reverse("branch_admin_dashboard") if is_admin else None,
    }

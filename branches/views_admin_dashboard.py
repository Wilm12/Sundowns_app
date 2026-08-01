from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from .models import Branch
from .services.branch_admin_dashboard import BranchAdminDashboardService


@login_required
def branch_admin_dashboard_view(request, branch_id=None):
    branch = None
    if branch_id is not None:
        branch = get_object_or_404(Branch, pk=branch_id)

    if not branch:
        branch = Branch.objects.filter(
            branch_roles__user=request.user,
            branch_roles__role='BRANCH_ADMIN',
            branch_roles__is_active=True,
        ).order_by('name').first()

    if not branch:
        raise PermissionDenied

    has_admin_access = branch.branch_roles.filter(
        user=request.user,
        role='BRANCH_ADMIN',
        is_active=True,
    ).exists()
    if not has_admin_access:
        raise PermissionDenied

    dashboard = BranchAdminDashboardService.get_dashboard(request.user, branch=branch)
    return render(request, 'branches/admin_dashboard.html', {'dashboard': dashboard})

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from .models import Branch
from .services.dashboard import BranchDashboardService


@login_required
def branch_dashboard_view(request, branch_id):
    branch = get_object_or_404(Branch, pk=branch_id)

    has_admin_access = branch.branch_roles.filter(
        user=request.user,
        role='BRANCH_ADMIN',
        is_active=True,
    ).exists()
    if not has_admin_access:
        raise PermissionDenied

    dashboard = BranchDashboardService.get_dashboard(branch)
    return render(request, 'branches/dashboard.html', {'dashboard': dashboard})

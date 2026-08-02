from django.shortcuts import render
from branches.services.branch_admin_dashboard import BranchAdminDashboardService
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from branches.models import BranchRole

@login_required
def branch_admin_dashboard_view(request):
    branch = request.user.branch

    is_admin = BranchRole.objects.filter(
        branch=branch,
        user=request.user,
        role=BranchRole.Role.BRANCH_ADMIN,
        is_active=True,
    ).exists()

    if not is_admin:
        return HttpResponseForbidden()

    dashboard = BranchAdminDashboardService.get_dashboard(request.user, branch)

    return render(
        request,
        "branches/admin_dashboard.html",
        {
            "dashboard": dashboard,
            "branch": branch,
        },
    )


from django.shortcuts import render
from branches.services.branch_admin_dashboard import BranchAdminDashboardService
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from branches.models import BranchRole
from branches.services.authorization import is_branch_admin

@login_required
def branch_admin_dashboard_view(request):
    branch = request.user.branch

    if branch is None and not request.user.is_superuser:
        branch_role = BranchRole.objects.filter(
            user=request.user,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        ).select_related("branch").first()
        branch = branch_role.branch if branch_role else None

    if branch is None:
        return HttpResponseForbidden("This user has no assigned branch and cannot access the branch admin dashboard.")

    if not is_branch_admin(request.user, branch):
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


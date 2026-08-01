from branches.models import BranchRole


class BranchAdminRequired(Exception):
    """Raised when a user is not authorized as a branch admin for the branch."""


def is_branch_admin(user, branch):
    if not user or not branch:
        return False
    return BranchRole.objects.filter(
        branch=branch,
        user=user,
        role=BranchRole.Role.BRANCH_ADMIN,
        is_active=True,
    ).exists()

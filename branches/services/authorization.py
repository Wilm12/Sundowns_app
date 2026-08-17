from branches.models import BranchRole


class BranchAdminRequired(Exception):
    """Raised when a user is not authorized as a branch admin for the branch."""


def is_branch_admin(user, branch=None):
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        if branch is None:
            return getattr(user, "branch_id", None) is not None

        branch_id = getattr(branch, "pk", branch)
        return bool(getattr(user, "branch_id", None)) and user.branch_id == branch_id

    if branch is None:
        return BranchRole.objects.filter(
            user=user,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        ).exists()

    return BranchRole.objects.filter(
        branch=branch,
        user=user,
        role=BranchRole.Role.BRANCH_ADMIN,
        is_active=True,
    ).exists()

from ..models import BranchRole


class BranchRoleAlreadyAssigned(Exception):
    """Raised when a user already holds the same active role in a branch."""


class AssignBranchRoleService:
    """Thin service for assigning operational roles to supporters within a branch."""

    @staticmethod
    def assign(branch, user, role, assigned_by=None):
        if BranchRole.objects.filter(
            branch=branch,
            user=user,
            role=role,
            is_active=True,
        ).exists():
            raise BranchRoleAlreadyAssigned(
                f"{user} already has the active role {role} in {branch}."
            )

        return BranchRole.objects.create(
            branch=branch,
            user=user,
            role=role,
            assigned_by=assigned_by,
            is_active=True,
        )

from ..models import BranchRole


class BranchRoleNotAssigned(Exception):
    """Raised when a role assignment does not exist or is already inactive."""


class RemoveBranchRoleService:
    """Soft-remove an active branch role assignment by deactivating it."""

    @staticmethod
    def remove(branch, user, role, removed_by=None):
        assignment = BranchRole.objects.filter(
            branch=branch,
            user=user,
            role=role,
            is_active=True,
        ).order_by("-assigned_at").first()

        if assignment is None:
            raise BranchRoleNotAssigned(
                f"{user} does not currently hold the role {role} in {branch}."
            )

        assignment.is_active = False
        assignment.save(update_fields=["is_active"])
        return assignment

import logging

logger = logging.getLogger(__name__)


def branch_role_assigned_handler(envelope):
    payload = envelope.payload or {}
    logger.info(
        "BranchRoleAssigned | branch=%s | supporter=%s | role=%s",
        payload.get("branch_id"),
        payload.get("supporter_id"),
        payload.get("role"),
    )


def branch_role_removed_handler(envelope):
    payload = envelope.payload or {}
    logger.info(
        "BranchRoleRemoved | branch=%s | supporter=%s | role=%s",
        payload.get("branch_id"),
        payload.get("supporter_id"),
        payload.get("role"),
    )

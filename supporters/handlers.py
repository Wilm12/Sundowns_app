import logging

logger = logging.getLogger(__name__)


def student_verification_requested_handler(envelope):
    payload = envelope.payload or {}
    logger.info(
        "StudentVerificationRequested | supporter=%s | verification=%s",
        payload.get("supporter_id"),
        payload.get("verification_id"),
    )


def student_verified_handler(envelope):
    payload = envelope.payload or {}
    logger.info(
        "StudentVerified | supporter=%s | verification=%s",
        payload.get("supporter_id"),
        payload.get("verification_id"),
    )


def student_verification_rejected_handler(envelope):
    payload = envelope.payload or {}
    logger.info(
        "StudentVerificationRejected | supporter=%s | verification=%s",
        payload.get("supporter_id"),
        payload.get("verification_id"),
    )

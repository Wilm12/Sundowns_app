import logging

logger = logging.getLogger(__name__)


def supporter_registered_handler(envelope):
    logger.info("SupporterRegistered | supporter=%s", envelope.payload.get("supporter_id"))


def student_verification_requested_handler(envelope):
    logger.info("StudentVerificationRequested | supporter=%s", envelope.payload.get("supporter_id"))


def student_verified_handler(envelope):
    logger.info("StudentVerified | supporter=%s", envelope.payload.get("supporter_id"))


def student_verification_rejected_handler(envelope):
    logger.info("StudentVerificationRejected | supporter=%s", envelope.payload.get("supporter_id"))


def eligibility_granted_handler(envelope):
    logger.info("EligibilityGranted | supporter=%s", envelope.payload.get("supporter_id"))


def eligibility_revoked_handler(envelope):
    logger.info("EligibilityRevoked | supporter=%s", envelope.payload.get("supporter_id"))

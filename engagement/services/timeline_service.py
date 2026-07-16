"""Timeline service for recording user engagement events.

This service module is responsible for recording engagement events
in the user's activity timeline. It provides a clean architecture
contract for future timeline persistence.
"""

import logging

logger = logging.getLogger(__name__)


def record_timeline_event(user, event, metadata=None):
    """Record an engagement event in the user's timeline.

    This function creates a record of a user's engagement event with
    associated metadata. Currently logs the event; future implementations
    will persist timeline data.

    Args:
        user: The user instance associated with the event.
        event (str): The type of engagement event being recorded.
        metadata (dict, optional): Additional event context. Defaults to None.
    """
    if metadata is None:
        metadata = {}

    logger.info(
        "Timeline Event: user_id=%s, event=%s, metadata=%s",
        user.id,
        event,
        metadata,
    )

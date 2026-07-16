"""Dispatcher services for the Engagement Engine.

This module exposes the public ``publish`` function which accepts an
``EngagementEventEnvelope`` and routes it to the registered handler. The
module contains no business logic, error-handling, retries or side-effects
other than dispatching the envelope to the mapped handler.
"""

import logging
from typing import Any

from engagement.envelope import EngagementEventEnvelope
from engagement.exceptions import HandlerNotRegisteredError
from engagement.registry import EVENT_HANDLERS


logger = logging.getLogger(__name__)


def publish(envelope: EngagementEventEnvelope) -> None:
    """Dispatch an engagement event envelope to its registered handler.

    Args:
        envelope: The ``EngagementEventEnvelope`` to publish.

    Raises:
        HandlerNotRegisteredError: If no handler is registered for
            ``envelope.event``.
    """
    if envelope.event not in EVENT_HANDLERS:
        raise HandlerNotRegisteredError(
            f"No handler registered for event: {envelope.event}"
        )

    handler = EVENT_HANDLERS[envelope.event]

    logger.info(
        "Publishing event: %s, correlation_id: %s",
        envelope.event.value,
        envelope.correlation_id,
    )

    handler(envelope)

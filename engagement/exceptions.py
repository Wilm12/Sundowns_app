"""Custom exceptions for the Engagement Engine.

This module defines a small hierarchy of exceptions used by the
engagement subsystem. Exceptions are lightweight declarations with
informative docstrings and no additional behaviour.
"""


class EngagementError(Exception):
    """Base exception for all Engagement Engine errors.

    Use this as the common base when catching engagement-specific
    failures across the platform.
    """


class HandlerNotRegisteredError(EngagementError):
    """Raised when an event is published with no registered handler.

    This indicates a configuration or registration problem where an
    event exists in the catalogue but no handler function has been
    associated with it in the registry.
    """


class InvalidEventEnvelopeError(EngagementError):
    """Raised when an invalid or malformed event envelope is supplied.

    Examples include missing required attributes or incorrect types on
    the envelope object passed to the dispatcher.
    """


class EventDispatchError(EngagementError):
    """Generic error raised when dispatching an event fails.

    This is reserved for upstream consumers that want to wrap lower-level
    exceptions occurring during handler execution.
    """

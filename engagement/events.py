"""Engagement event catalogue.

This module defines the platform event vocabulary for the Engagement
module. The events are intentionally limited to declarations and do not
include any publish, dispatch, or handler logic.
"""

from enum import Enum


class EngagementEvent(Enum):
    """Platform events that the Engagement module can react to."""

    # Membership events
    MEMBER_REGISTERED = "member_registered"
    MEMBERSHIP_ACTIVATED = "membership_activated"
    MEMBERSHIP_RENEWED = "membership_renewed"
    MEMBERSHIP_EXPIRED = "membership_expired"
    MEMBERSHIP_TIER_CHANGED = "membership_tier_changed"

    # Payment events
    PAYMENT_SUCCESSFUL = "payment_successful"
    PAYMENT_FAILED = "payment_failed"
    REFUND_ISSUED = "refund_issued"

    # Match events
    MATCH_PUBLISHED = "match_published"
    MATCH_UPDATED = "match_updated"
    MATCH_CANCELLED = "match_cancelled"

    # Ticket events
    TICKET_BOOKED = "ticket_booked"
    TICKET_CANCELLED = "ticket_cancelled"
    TICKET_VERIFIED = "ticket_verified"
    TICKET_EXPIRED = "ticket_expired"

    # Transport events
    TRANSPORT_BOOKED = "transport_booked"
    TRANSPORT_CANCELLED = "transport_cancelled"
    TRANSPORT_BOARDED = "transport_boarded"

    # Reward events
    POINTS_AWARDED = "points_awarded"
    REWARD_REDEEMED = "reward_redeemed"
    PROMOTION_COMPLETED = "promotion_completed"

    # Branch events
    BRANCH_JOINED = "branch_joined"
    BRANCH_CHANGED = "branch_changed"
    BRANCH_MILESTONE_REACHED = "branch_milestone_reached"
    BRANCH_ROLE_ASSIGNED = "branch_role_assigned"
    BRANCH_ROLE_REMOVED = "branch_role_removed"

    # Supporter events
    STUDENT_VERIFICATION_REQUESTED = "student_verification_requested"
    STUDENT_VERIFIED = "student_verified"
    STUDENT_VERIFICATION_REJECTED = "student_verification_rejected"

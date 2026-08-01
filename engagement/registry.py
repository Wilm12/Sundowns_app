"""Engagement event-to-handler registry.

This module maps platform engagement events to handler functions. It is
intentionally limited to declaration and does not include dispatcher or
business logic.
"""

from engagement.events import EngagementEvent
from engagement.handlers import (
    membership_activated_handler,
    member_registered_handler,
    payment_failed_handler,
    payment_successful_handler,
    refund_issued_handler,
    match_published_handler,
    match_updated_handler,
    match_cancelled_handler,
    ticket_booked_handler,
    ticket_cancelled_handler,
    ticket_verified_handler,
    ticket_expired_handler,
    transport_booked_handler,
    transport_cancelled_handler,
    transport_boarded_handler,
    points_awarded_handler,
    reward_redeemed_handler,
    promotion_completed_handler,
    branch_joined_handler,
    branch_changed_handler,
    branch_milestone_reached_handler,
)
from branches.handlers import (
    branch_role_assigned_handler,
    branch_role_removed_handler,
)
from supporters.handlers import (
    eligibility_granted_handler,
    eligibility_revoked_handler,
    student_verification_rejected_handler,
    student_verification_requested_handler,
    student_verified_handler,
)
from journeys.handlers import (
    attendance_recorded_handler,
    journey_booked_handler,
    journey_opened_handler,
    ticket_allocated_handler,
    ticket_collected_handler,
)


EVENT_HANDLERS = {
    EngagementEvent.MEMBER_REGISTERED: member_registered_handler,
    EngagementEvent.MEMBERSHIP_ACTIVATED: membership_activated_handler,
    EngagementEvent.PAYMENT_SUCCESSFUL: payment_successful_handler,
    EngagementEvent.PAYMENT_FAILED: payment_failed_handler,
    EngagementEvent.REFUND_ISSUED: refund_issued_handler,
    EngagementEvent.MATCH_PUBLISHED: match_published_handler,
    EngagementEvent.MATCH_UPDATED: match_updated_handler,
    EngagementEvent.MATCH_CANCELLED: match_cancelled_handler,
    EngagementEvent.TICKET_BOOKED: ticket_booked_handler,
    EngagementEvent.TICKET_CANCELLED: ticket_cancelled_handler,
    EngagementEvent.TICKET_VERIFIED: ticket_verified_handler,
    EngagementEvent.TICKET_EXPIRED: ticket_expired_handler,
    EngagementEvent.TRANSPORT_BOOKED: transport_booked_handler,
    EngagementEvent.TRANSPORT_CANCELLED: transport_cancelled_handler,
    EngagementEvent.TRANSPORT_BOARDED: transport_boarded_handler,
    EngagementEvent.POINTS_AWARDED: points_awarded_handler,
    EngagementEvent.REWARD_REDEEMED: reward_redeemed_handler,
    EngagementEvent.PROMOTION_COMPLETED: promotion_completed_handler,
    EngagementEvent.BRANCH_JOINED: branch_joined_handler,
    EngagementEvent.BRANCH_CHANGED: branch_changed_handler,
    EngagementEvent.BRANCH_MILESTONE_REACHED: branch_milestone_reached_handler,
    EngagementEvent.BRANCH_ROLE_ASSIGNED: branch_role_assigned_handler,
    EngagementEvent.BRANCH_ROLE_REMOVED: branch_role_removed_handler,
    EngagementEvent.STUDENT_VERIFICATION_REQUESTED: student_verification_requested_handler,
    EngagementEvent.STUDENT_VERIFIED: student_verified_handler,
    EngagementEvent.STUDENT_VERIFICATION_REJECTED: student_verification_rejected_handler,
    EngagementEvent.ELIGIBILITY_GRANTED: eligibility_granted_handler,
    EngagementEvent.ELIGIBILITY_REVOKED: eligibility_revoked_handler,
    EngagementEvent.JOURNEY_OPENED: journey_opened_handler,
    EngagementEvent.JOURNEY_BOOKED: journey_booked_handler,
    EngagementEvent.TICKET_ALLOCATED: ticket_allocated_handler,
    EngagementEvent.TICKET_COLLECTED: ticket_collected_handler,
    EngagementEvent.ATTENDANCE_RECORDED: attendance_recorded_handler,
}

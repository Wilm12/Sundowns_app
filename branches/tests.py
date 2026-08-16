from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from engagement.events import EngagementEvent

from journeys.models import Journey, JourneyStatus
from matches.models import Match
from supporters.models import EligibilityReason, SupporterEligibility, StudentVerification, StudentVerificationStatus
from ticketing.models import Ticket
from users.models import User

from .models import Branch, BranchPolicy, BranchRole, BranchStatus, CommitteeActivity, CommitteeAction, CommitteePosition, MatchAllocation
from .serializers import BranchPolicySerializer, BranchRoleSerializer, BranchSerializer
from .services.assign_branch_role import AssignBranchRoleService, BranchRoleAlreadyAssigned
from .services.branch_admin_dashboard import BranchAdminDashboardService
from .services.committee import CommitteeService
from .services.promote_branch_admin import BranchAdminAlreadyAssigned, PromoteBranchAdminService, UserNotInBranch
from .services.remove_branch_admin import LastBranchAdminRemovalError, RemoveBranchAdminService
from .services.remove_branch_role import BranchRoleNotAssigned, RemoveBranchRoleService
from branches.services.authorization import BranchAdminRequired, is_branch_admin


class BranchAdminDashboardTests(TestCase):
    def test_branch_admin_helper_returns_true_for_authorized_users(self):
        branch = Branch.objects.create(name="Authorization Branch")
        admin = self._create_user(username="authorization-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.assertTrue(is_branch_admin(admin))
        self.assertTrue(is_branch_admin(admin, branch))

    def test_dashboard_metrics_are_correct(self):
        branch = Branch.objects.create(name="Metrics Branch")
        admin = self._create_user(username="metrics-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter_one = self._create_user(username="metrics-supporter-one")
        supporter_one.branch = branch
        supporter_one.save(update_fields=["branch"])
        BranchRole.objects.create(
            branch=branch,
            user=supporter_one,
            role=BranchRole.Role.MEMBER,
            is_active=True,
        )

        supporter_two = self._create_user(username="metrics-supporter-two")
        supporter_two.branch = branch
        supporter_two.save(update_fields=["branch"])
        BranchRole.objects.create(
            branch=branch,
            user=supporter_two,
            role=BranchRole.Role.MEMBER,
            is_active=True,
        )

        supporter_three = self._create_user(username="metrics-supporter-three")
        supporter_three.branch = branch
        supporter_three.save(update_fields=["branch"])

        StudentVerification.objects.create(user=supporter_one, student_number="u10001", university="TUKS", status=StudentVerificationStatus.VERIFIED)
        StudentVerification.objects.create(user=supporter_two, student_number="u10002", university="TUKS", status=StudentVerificationStatus.PENDING)
        SupporterEligibility.objects.create(supporter=supporter_one, is_eligible=True, reason=EligibilityReason.VERIFIED)
        SupporterEligibility.objects.create(supporter=supporter_two, is_eligible=False, reason=EligibilityReason.VERIFICATION_PENDING)

        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Orlando Pirates")
        Journey.objects.create(supporter=supporter_one, branch=branch, match=match, status=JourneyStatus.BOOKED)
        Journey.objects.create(supporter=supporter_two, branch=branch, match=match, status=JourneyStatus.MATCH_ATTENDED)
        Journey.objects.create(supporter=supporter_three, branch=branch, match=match, status=JourneyStatus.TICKET_READY)

        dashboard = BranchAdminDashboardService.get_dashboard(admin, branch=branch)

        self.assertEqual(dashboard["supporter_metrics"]["total_supporters"], 4)
        self.assertEqual(dashboard["supporter_metrics"]["verified_supporters"], 1)
        self.assertEqual(dashboard["supporter_metrics"]["eligible_supporters"], 1)
        self.assertEqual(dashboard["supporter_metrics"]["active_members"], 1)
        self.assertEqual(dashboard["journey_metrics"]["allocated_count"], 2)
        self.assertEqual(dashboard["journey_metrics"]["booked_count"], 3)
        self.assertEqual(dashboard["journey_metrics"]["pending_count"], 1)
        self.assertEqual(dashboard["journey_metrics"]["attended_count"], 1)

    def test_gate_redemption_redirects_unverified_supporter_to_verification(self):
        branch = Branch.objects.create(name="Gate Redirect Branch")
        admin = self._create_user(username="gate-redirect-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="gate-redirect-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Cape Town", opponent="Mamelodi Sundowns")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        StudentVerification.objects.create(user=supporter, student_number="u90001", university="UCT", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            reverse("match_operations_console", args=[branch.pk, match.pk]),
            data={"action": "redeem", "collection_code": "4827"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("branch_supporter_verification", args=[branch.pk, supporter.pk]), response.url)
        self.assertIn("next=ticket-collection", response.url)
        self.assertIn("code=4827", response.url)
        self.assertEqual(journey.status, JourneyStatus.BOOKED)

    def test_verification_flow_creates_missing_record_and_redeems_ticket(self):
        branch = Branch.objects.create(name="Verification Auto Redemption Branch")
        admin = self._create_user(username="verification-auto-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="verification-auto-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Durban", opponent="Kaizer Chiefs")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            f"{reverse('branch_supporter_verification', args=[branch.pk, supporter.pk])}?next=ticket-collection&code=4827&match_id={match.pk}",
            data={},
            follow=True,
        )

        self.assertRedirects(response, reverse("match_operations_console", args=[branch.pk, match.pk]))
        self.assertContains(response, "Supporter verified and ticket redeemed successfully.")
        verification = StudentVerification.objects.get(user=supporter)
        journey.refresh_from_db()
        self.assertEqual(verification.status, StudentVerificationStatus.APPROVED)
        self.assertEqual(journey.status, JourneyStatus.MATCH_ATTENDED)
        self.assertEqual(journey.attended_by, admin)

    def test_verification_redirect_completes_redemption_after_verification(self):
        branch = Branch.objects.create(name="Verification Redemption Branch")
        admin = self._create_user(username="verification-redemption-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="verification-redemption-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Durban", opponent="Kaizer Chiefs")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        verification = StudentVerification.objects.create(user=supporter, student_number="u90002", university="Wits", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            f"{reverse('branch_supporter_verification', args=[branch.pk, supporter.pk])}?next=ticket-collection&code=4827&match_id={match.pk}",
            data={},
        )

        self.assertEqual(response.status_code, 302)
        verification.refresh_from_db()
        journey.refresh_from_db()
        self.assertEqual(verification.status, StudentVerificationStatus.APPROVED)
        self.assertEqual(journey.status, JourneyStatus.MATCH_ATTENDED)
        self.assertEqual(journey.attended_by, admin)

    def test_verification_form_post_uses_hidden_gate_redemption_values(self):
        branch = Branch.objects.create(name="Verification Form Branch")
        admin = self._create_user(username="verification-form-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="verification-form-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Mthatha", opponent="Golden Arrows")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        verification = StudentVerification.objects.create(user=supporter, student_number="u90003", university="UCT", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            reverse("branch_supporter_verification", args=[branch.pk, supporter.pk]),
            data={"next": "ticket-collection", "code": "4827", "match_id": match.pk},
        )

        self.assertEqual(response.status_code, 302)
        verification.refresh_from_db()
        journey.refresh_from_db()
        self.assertEqual(verification.status, StudentVerificationStatus.APPROVED)
        self.assertEqual(journey.status, JourneyStatus.MATCH_ATTENDED)
        self.assertEqual(journey.attended_by, admin)

    def test_redemption_redirects_unverified_supporter_to_verification(self):
        branch = Branch.objects.create(name="Gate Redirect Branch")
        admin = self._create_user(username="gate-redirect-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="gate-redirect-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Cape Town", opponent="Mamelodi Sundowns")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        StudentVerification.objects.create(user=supporter, student_number="u90001", university="UCT", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            reverse("match_operations_console", args=[branch.pk, match.pk]),
            data={"action": "redeem", "collection_code": "4827"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("branch_supporter_verification", args=[branch.pk, supporter.pk]), response.url)
        self.assertIn("next=ticket-collection", response.url)
        self.assertIn("code=4827", response.url)
        self.assertEqual(journey.status, JourneyStatus.BOOKED)

    def test_verification_redirect_completes_redemption_after_verification(self):
        branch = Branch.objects.create(name="Verification Redemption Branch")
        admin = self._create_user(username="verification-redemption-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="verification-redemption-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Durban", opponent="Kaizer Chiefs")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        verification = StudentVerification.objects.create(user=supporter, student_number="u90002", university="Wits", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            f"{reverse('branch_supporter_verification', args=[branch.pk, supporter.pk])}?next=ticket-collection&code=4827&match_id={match.pk}",
            data={},
        )

        self.assertEqual(response.status_code, 302)
        verification.refresh_from_db()
        journey.refresh_from_db()
        self.assertEqual(verification.status, StudentVerificationStatus.APPROVED)
        self.assertEqual(journey.status, JourneyStatus.MATCH_ATTENDED)
        self.assertEqual(journey.attended_by, admin)

    def test_branch_admin_dashboard_displays_operational_current_match_report(self):
        """Landing dashboard shows operational report: Allocated, Booked, Pending, Attended."""
        branch = Branch.objects.create(name="Operational Branch")
        admin = self._create_user(username="operational-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter_one = self._create_user(username="op-supp-one")
        supporter_two = self._create_user(username="op-supp-two")
        supporter_three = self._create_user(username="op-supp-three")
        supporter_four = self._create_user(username="op-supp-four")

        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Kaizer Chiefs")

        # Booked (not collected)
        Journey.objects.create(supporter=supporter_one, branch=branch, match=match, status=JourneyStatus.BOOKED)
        # Ticket ready (pending)
        Journey.objects.create(supporter=supporter_two, branch=branch, match=match, status=JourneyStatus.TICKET_READY)
        # Ticket collected (counts as attended)
        Journey.objects.create(supporter=supporter_three, branch=branch, match=match, status=JourneyStatus.TICKET_COLLECTED)
        # Match attended
        Journey.objects.create(supporter=supporter_four, branch=branch, match=match, status=JourneyStatus.MATCH_ATTENDED)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_admin_dashboard"))

        # Operational report should be visible
        self.assertContains(response, "Current Match Report")
        self.assertContains(response, "Kaizer Chiefs")
        
        # Operational metrics should be visible
        self.assertContains(response, "Allocated")
        self.assertContains(response, "Booked")
        self.assertContains(response, "Pending")
        self.assertContains(response, "Attended")

    def test_branch_admin_dashboard_does_not_show_analytics_cards_inline(self):
        """Landing dashboard must NOT display the Branch Performance analytics cards directly."""
        branch = Branch.objects.create(name="No Analytics Branch")
        admin = self._create_user(username="no-analytics-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="no-analytics-supp")
        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Pirates")
        Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_admin_dashboard"))
        content = response.content.decode()

        # Analytics cards should NOT appear on landing dashboard
        self.assertNotContains(response, "Current Match Performance")
        self.assertNotContains(response, "Performance Across Matches")
        self.assertNotContains(response, "Supporters Booked")
        self.assertNotContains(response, "Supporters Attended")
        self.assertNotContains(response, "Verification Completed")
        self.assertNotContains(response, "Attendance Rate")

    def test_branch_performance_page_loads_and_shows_only_current_branch_analytics(self):
        branch = Branch.objects.create(name="Performance Analytics Branch")
        other_branch = Branch.objects.create(name="Other Analytics Branch")
        admin = self._create_user(username="perf-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter_one = self._create_user(username="perf-supp-one")
        supporter_two = self._create_user(username="perf-supp-two")
        other_supporter = self._create_user(username="perf-other-supp")

        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Kaizer Chiefs")
        other_match = Match.objects.create(date=timezone.now() + timezone.timedelta(days=5), location="Ellis Park", opponent="Lions")

        Journey.objects.create(supporter=supporter_one, branch=branch, match=match, status=JourneyStatus.BOOKED)
        Journey.objects.create(supporter=supporter_two, branch=branch, match=match, status=JourneyStatus.TICKET_COLLECTED)
        Journey.objects.create(supporter=other_supporter, branch=other_branch, match=match, status=JourneyStatus.MATCH_ATTENDED)
        Journey.objects.create(supporter=other_supporter, branch=other_branch, match=other_match, status=JourneyStatus.BOOKED)

        StudentVerification.objects.create(user=supporter_one, student_number="BPA1", university="UP", status=StudentVerificationStatus.VERIFIED)
        StudentVerification.objects.create(user=supporter_two, student_number="BPA2", university="UP", status=StudentVerificationStatus.APPROVED)
        StudentVerification.objects.create(user=other_supporter, student_number="BPA3", university="Wits", status=StudentVerificationStatus.VERIFIED)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_performance", args=[branch.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Branch Performance")
        self.assertContains(response, branch.name)
        self.assertContains(response, "Current Match Performance")
        self.assertContains(response, "Performance Across Matches")
        self.assertContains(response, "Supporters Booked")
        self.assertContains(response, "Supporters Attended")
        self.assertContains(response, "Attendance Rate")
        self.assertContains(response, "Verification Completed")
        self.assertContains(response, "Kaizer Chiefs")
        self.assertNotContains(response, other_branch.name)

    def test_dashboard_reports_card_shows_branch_performance_button(self):
        """Landing dashboard Reports section must show 'Branch Performance' button."""
        branch = Branch.objects.create(name="Reports Button Branch")
        admin = self._create_user(username="reports-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_admin_dashboard"))

        # Should have "Branch Performance" button
        self.assertContains(response, "Branch Performance")
        # Should NOT have "Attendance Report" button
        self.assertNotContains(response, "Attendance Report")
        # Button should link to dedicated performance page
        self.assertContains(response, f'href="{reverse("branch_performance", args=[branch.id])}"')

    def test_branch_performance_back_to_dashboard_link_returns_to_landing_dashboard(self):
        branch = Branch.objects.create(name="Back Link Branch")
        admin = self._create_user(username="back-link-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.client.force_login(admin)
        performance_response = self.client.get(reverse("branch_performance", args=[branch.id]))

        self.assertEqual(performance_response.status_code, 200)
        dashboard_url = reverse("branch_admin_dashboard")
        self.assertContains(performance_response, f'href="{dashboard_url}"')

        dashboard_response = self.client.get(dashboard_url)
        self.assertEqual(dashboard_response.status_code, 200)

    def test_branch_performance_page_requires_branch_admin_authorization(self):
        branch = Branch.objects.create(name="Auth Test Branch")
        supporter = self._create_user(username="auth-supp")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        self.client.force_login(supporter)
        response = self.client.get(reverse("branch_performance", args=[branch.id]))

        self.assertEqual(response.status_code, 403)

    def test_dashboard_uses_branch_operational_match_when_available(self):
        branch = Branch.objects.create(name="Operational Match Branch")
        admin = self._create_user(username="operational-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="operational-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        future_match = Match.objects.create(date=timezone.now() + timezone.timedelta(days=7), location="Loftus", opponent="Future Opponent")
        operational_match = Match.objects.create(date=timezone.now() - timezone.timedelta(days=1), location="Loftus", opponent="Current Opponent")
        Journey.objects.create(supporter=supporter, branch=branch, match=operational_match, status=JourneyStatus.BOOKED)

        dashboard = BranchAdminDashboardService.get_dashboard(admin, branch=branch)

        self.assertEqual(dashboard["dashboard_match"], operational_match)
        self.assertEqual(dashboard["dashboard_match"].opponent, "Current Opponent")

    def test_match_management_page_loads_and_publish_sets_operational_match(self):
        branch = Branch.objects.create(name="Match Management Branch")
        admin = self._create_user(username="match-management-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_matches_manage", args=[branch.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Match Management")

        match = Match.objects.create(date=timezone.now() + timezone.timedelta(days=2), location="Loftus", opponent="Orlando Pirates")
        publish_response = self.client.get(reverse("branch_match_publish", args=[branch.pk, match.pk]))
        self.assertEqual(publish_response.status_code, 302)
        branch.refresh_from_db()
        self.assertEqual(branch.operational_match, match)

    def test_branch_match_allocation_updates_match_management_and_dashboard_metric(self):
        branch = Branch.objects.create(name="Allocation Branch")
        admin = self._create_user(username="allocation-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="allocation-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now() + timezone.timedelta(days=5), location="Loftus", opponent="Kaizer Chiefs")
        Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        self.client.force_login(admin)
        response = self.client.post(
            reverse("branch_committee", args=[branch.pk]),
            data={
                "match_submit": "1",
                "opponent": "Kaizer Chiefs",
                "date": (timezone.now() + timezone.timedelta(days=6)).strftime("%Y-%m-%d"),
                "location": "Loftus",
                "ticket_collection_timeframe": "18:00-19:00",
                "gate_number": "Gate 3",
                "published": "on",
                f"allocation_{branch.pk}": "18",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        allocation = branch.match_allocations.get(match__opponent="Kaizer Chiefs")
        self.assertEqual(allocation.allocated_tickets, 18)
        self.assertContains(response, "Match created and published as the branch operational match.")

        dashboard = BranchAdminDashboardService.get_dashboard(admin, branch=branch)
        self.assertEqual(dashboard["journey_metrics"]["allocated_count"], 18)

    def test_match_management_allocation_form_renders_and_edit_updates_values(self):
        branch = Branch.objects.create(name="Allocation Edit Branch")
        admin = self._create_user(username="allocation-edit-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        match = Match.objects.create(date=timezone.now() + timezone.timedelta(days=4), location="Loftus", opponent="Cape Town City")
        MatchAllocation.objects.create(branch=branch, match=match, allocated_tickets=12)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_matches_manage", args=[branch.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Branch Ticket Allocations")
        self.assertContains(response, f'name="allocation_{branch.pk}"')

        edit_response = self.client.get(reverse("branch_match_edit", args=[branch.pk, match.pk]))
        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, "Branch Ticket Allocations")

        update_response = self.client.post(
            reverse("branch_match_edit", args=[branch.pk, match.pk]),
            data={
                "opponent": "Cape Town City",
                "date": (timezone.now() + timezone.timedelta(days=5)).strftime("%Y-%m-%d"),
                "location": "Loftus",
                "ticket_collection_timeframe": "17:00-18:00",
                "gate_number": "Gate 5",
                "published": "on",
                f"allocation_{branch.pk}": "28",
            },
            follow=True,
        )

        self.assertEqual(update_response.status_code, 200)
        match.refresh_from_db()
        allocation = MatchAllocation.objects.get(branch=branch, match=match)
        self.assertEqual(allocation.allocated_tickets, 28)
        self.assertContains(update_response, "Match updated successfully.")

    def test_edit_match_action_links_to_existing_edit_page_and_requires_authorization(self):
        branch = Branch.objects.create(name="Edit Match Branch")
        admin = self._create_user(username="edit-match-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        match = Match.objects.create(date=timezone.now() + timezone.timedelta(days=3), location="Loftus", opponent="Cape Town City")
        branch.operational_match = match
        branch.save(update_fields=["operational_match"])

        self.client.force_login(admin)
        committee_response = self.client.get(reverse("branch_committee", args=[branch.pk]))

        self.assertEqual(committee_response.status_code, 200)
        self.assertContains(committee_response, "Edit Match")
        edit_url = reverse("branch_match_edit", args=[branch.pk, match.pk])
        self.assertContains(committee_response, f'href="{edit_url}"')

        edit_response = self.client.get(edit_url)
        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, "Edit Match")

        supporter = self._create_user(username="edit-match-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        self.client.force_login(supporter)
        forbidden_response = self.client.get(edit_url)
        self.assertEqual(forbidden_response.status_code, 403)

    def test_dashboard_renders_leadership_positions_and_reports_before_committee(self):
        branch = Branch.objects.create(name="Leadership Branch")
        admin = self._create_user(username="leadership-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        admin_role = BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        CommitteePosition.objects.create(branch=branch, branch_role=admin_role, position=CommitteePosition.Position.CHAIRPERSON, created_by=admin)

        supporter = self._create_user(username="leadership-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Orlando Pirates")
        Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_admin_dashboard"))
        content = response.content.decode()

        self.assertContains(response, "Reports")
        self.assertContains(response, "Leadership")
        self.assertContains(response, "Chairperson")
        self.assertNotContains(response, "Collected")
        self.assertLess(content.index("Reports"), content.index("Committee"))

    def test_dashboard_assigns_default_chairperson_when_no_leadership_positions_exist(self):
        branch = Branch.objects.create(name="Auto Chair Branch")
        admin = self._create_user(username="auto-chair-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        dashboard = BranchAdminDashboardService.get_dashboard(admin, branch=branch)

        self.assertTrue(
            CommitteePosition.objects.filter(
                branch=branch,
                branch_role__user=admin,
                position=CommitteePosition.Position.CHAIRPERSON,
            ).exists()
        )
        self.assertIn("Chairperson", dashboard["committee_members"][0]["position"])

    def test_dashboard_renders_single_reports_and_recent_activity_sections(self):
        branch = Branch.objects.create(name="Layout Branch")
        admin = self._create_user(username="layout-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_admin_dashboard"))
        content = response.content.decode()

        self.assertEqual(content.count("Quick access to branch reporting"), 1)
        self.assertEqual(content.count("Leadership Panel"), 1)

    def test_branch_operations_page_has_required_sections_in_order(self):
        branch = Branch.objects.create(name="Operations Layout Branch")
        admin = self._create_user(username="ops-layout-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_committee", args=[branch.pk]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        required_sections = [
            "Supporter Verification",
            "Match Management",
            "Committee Members",
            "Leadership Assignment",
            "Branch Administrators",
            "Recent Activity",
        ]
        for label in required_sections:
            self.assertIn(label, content)

        self.assertNotIn("Leadership Panel", content)

        positions = [content.index(label) for label in required_sections]
        self.assertEqual(positions, sorted(positions))

    def test_promotion_and_committee_position_management_workflow(self):
        branch = Branch.objects.create(name="Committee Workflow Branch")
        admin = self._create_user(username="committee-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="committee-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        promoted = PromoteBranchAdminService.promote(branch, supporter, admin)
        self.assertEqual(promoted.role, BranchRole.Role.BRANCH_ADMIN)

        role = BranchRole.objects.get(branch=branch, user=supporter, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        CommitteePosition.objects.create(branch=branch, branch_role=role, position=CommitteePosition.Position.SECRETARY, created_by=admin)
        committee_position = CommitteePosition.objects.get(branch=branch, branch_role=role)
        committee_position.position = CommitteePosition.Position.CHAIRPERSON
        committee_position.save(update_fields=["position"])

        self.assertEqual(committee_position.position, CommitteePosition.Position.CHAIRPERSON)

        committee_position.delete()
        self.assertFalse(CommitteePosition.objects.filter(branch=branch, branch_role=role).exists())

    def test_branch_performance_page_loads_and_shows_only_current_branch_analytics(self):
        branch = Branch.objects.create(name="Performance Analytics Branch")
        other_branch = Branch.objects.create(name="Other Analytics Branch")
        admin = self._create_user(username="perf-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter_one = self._create_user(username="perf-supp-one")
        supporter_two = self._create_user(username="perf-supp-two")
        other_supporter = self._create_user(username="perf-other-supp")

        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Kaizer Chiefs")
        other_match = Match.objects.create(date=timezone.now() + timezone.timedelta(days=5), location="Ellis Park", opponent="Lions")

        Journey.objects.create(supporter=supporter_one, branch=branch, match=match, status=JourneyStatus.BOOKED)
        Journey.objects.create(supporter=supporter_two, branch=branch, match=match, status=JourneyStatus.TICKET_COLLECTED)
        Journey.objects.create(supporter=other_supporter, branch=other_branch, match=match, status=JourneyStatus.MATCH_ATTENDED)
        Journey.objects.create(supporter=other_supporter, branch=other_branch, match=other_match, status=JourneyStatus.BOOKED)

        StudentVerification.objects.create(user=supporter_one, student_number="BPA1", university="UP", status=StudentVerificationStatus.VERIFIED)
        StudentVerification.objects.create(user=supporter_two, student_number="BPA2", university="UP", status=StudentVerificationStatus.APPROVED)
        StudentVerification.objects.create(user=other_supporter, student_number="BPA3", university="Wits", status=StudentVerificationStatus.VERIFIED)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_performance", args=[branch.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Branch Performance")
        self.assertContains(response, branch.name)
        self.assertContains(response, "Current Match Performance")
        self.assertContains(response, "Performance Across Matches")
        self.assertContains(response, "Supporters Booked")
        self.assertContains(response, "Supporters Attended")
        self.assertContains(response, "Attendance Rate")
        self.assertContains(response, "Verification Completed")
        self.assertContains(response, "Kaizer Chiefs")
        self.assertNotContains(response, other_branch.name)

    def test_branch_performance_page_requires_branch_admin_authorization(self):
        branch = Branch.objects.create(name="Auth Test Branch")
        supporter = self._create_user(username="auth-supp")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        self.client.force_login(supporter)
        response = self.client.get(reverse("branch_performance", args=[branch.id]))

        self.assertEqual(response.status_code, 403)

    def test_dashboard_reports_card_shows_branch_performance_button(self):
        branch = Branch.objects.create(name="Reports Button Branch")
        admin = self._create_user(username="reports-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_admin_dashboard"))

        self.assertContains(response, "Branch Performance")
        self.assertNotContains(response, "Attendance Report")
        self.assertContains(response, f'href="{reverse("branch_performance", args=[branch.id])}"')

    def test_last_branch_admin_cannot_be_removed(self):
        branch = Branch.objects.create(name="Last Admin Branch")
        admin = self._create_user(username="last-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        with self.assertRaises(LastBranchAdminRemovalError):
            RemoveBranchAdminService.remove(branch, admin, admin)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )

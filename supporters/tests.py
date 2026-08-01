from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from engagement.events import EngagementEvent

from .models import StudentVerification, StudentVerificationStatus
from .services.reject_student_verification import RejectStudentVerificationService, VerificationAlreadyProcessed
from .services.request_student_verification import DuplicatePendingVerification, RequestStudentVerificationService
from .services.list_pending_verifications import ListPendingVerificationsService
from .services.verify_student import ActiveVerificationExists, VerifyStudentService


class StudentVerificationServiceTests(TestCase):
    def test_create_pending_verification(self):
        user = self._create_user(username="pending-user")

        verification = StudentVerification.objects.create(
            user=user,
            student_number="12345",
            university="UCT",
        )

        self.assertEqual(verification.status, StudentVerificationStatus.PENDING)
        self.assertIsNone(verification.verified_at)
        self.assertIsNone(verification.expires_at)

    def test_approve_verification(self):
        user = self._create_user(username="verify-user")
        verification = StudentVerification.objects.create(
            user=user,
            student_number="54321",
            university="Wits",
        )
        verifier = self._create_user(username="verifier-user")

        updated_verification = VerifyStudentService.verify(verification, verifier)

        self.assertEqual(updated_verification.status, StudentVerificationStatus.VERIFIED)
        self.assertIsNotNone(updated_verification.verified_at)
        self.assertIsNotNone(updated_verification.expires_at)
        self.assertEqual(updated_verification.verified_by, verifier)

    def test_verified_at_is_populated(self):
        user = self._create_user(username="verified-at-user")
        verification = StudentVerification.objects.create(
            user=user,
            student_number="11111",
            university="UJ",
        )
        verifier = self._create_user(username="verifier-at-user")

        VerifyStudentService.verify(verification, verifier)

        self.assertIsNotNone(StudentVerification.objects.get(pk=verification.pk).verified_at)

    def test_expires_at_is_one_year_in_future(self):
        user = self._create_user(username="expiry-user")
        verification = StudentVerification.objects.create(
            user=user,
            student_number="22222",
            university="NWU",
        )
        verifier = self._create_user(username="expiry-verifier")

        VerifyStudentService.verify(verification, verifier)

        verification.refresh_from_db()
        self.assertAlmostEqual(
            (verification.expires_at - verification.verified_at).days,
            365,
            delta=1,
        )

    def test_verifier_is_recorded(self):
        user = self._create_user(username="verifier-record-user")
        verification = StudentVerification.objects.create(
            user=user,
            student_number="33333",
            university="UFS",
        )
        verifier = self._create_user(username="record-verifier")

        VerifyStudentService.verify(verification, verifier)

        verification.refresh_from_db()
        self.assertEqual(verification.verified_by, verifier)

    def test_duplicate_active_verification_raises(self):
        user = self._create_user(username="duplicate-user")
        verifier = self._create_user(username="duplicate-verifier")

        first_verification = StudentVerification.objects.create(
            user=user,
            student_number="44444",
            university="UP",
            status=StudentVerificationStatus.VERIFIED,
            verified_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=90),
            verified_by=verifier,
        )
        second_verification = StudentVerification.objects.create(
            user=user,
            student_number="55555",
            university="UP",
            status=StudentVerificationStatus.PENDING,
        )

        with self.assertRaises(ActiveVerificationExists):
            VerifyStudentService.verify(second_verification, verifier)

    def test_expired_verification_allows_new_verification(self):
        user = self._create_user(username="expired-user")
        verifier = self._create_user(username="expired-verifier")

        expired_verification = StudentVerification.objects.create(
            user=user,
            student_number="66666",
            university="RU",
            status=StudentVerificationStatus.VERIFIED,
            verified_at=timezone.now() - timedelta(days=400),
            expires_at=timezone.now() - timedelta(days=1),
            verified_by=verifier,
        )
        new_verification = StudentVerification.objects.create(
            user=user,
            student_number="77777",
            university="RU",
            status=StudentVerificationStatus.PENDING,
        )

        updated_verification = VerifyStudentService.verify(new_verification, verifier)

        self.assertEqual(updated_verification.status, StudentVerificationStatus.VERIFIED)
        self.assertEqual(updated_verification.user, user)

    @patch("supporters.services.request_student_verification.publish")
    def test_create_pending_verification_request(self, mock_publish):
        user = self._create_user(username="request-user")

        verification = RequestStudentVerificationService.request(
            user=user,
            student_number="10001",
            university="UCT",
            requested_by=user,
        )

        self.assertEqual(verification.status, StudentVerificationStatus.PENDING)
        self.assertEqual(mock_publish.call_count, 1)
        envelope = mock_publish.call_args.args[0]
        self.assertEqual(envelope.event, EngagementEvent.STUDENT_VERIFICATION_REQUESTED)
        self.assertEqual(envelope.payload["supporter_id"], user.pk)

    @patch("supporters.services.request_student_verification.publish")
    def test_duplicate_pending_request_is_blocked(self, mock_publish):
        user = self._create_user(username="duplicate-request-user")
        RequestStudentVerificationService.request(user=user, student_number="10002", university="UJ")

        with self.assertRaises(DuplicatePendingVerification):
            RequestStudentVerificationService.request(user=user, student_number="10003", university="UCT")

        self.assertEqual(mock_publish.call_count, 1)

    @patch("supporters.services.verify_student.publish")
    def test_approve_verification_publishes_student_verified(self, mock_publish):
        user = self._create_user(username="approve-publish-user")
        verification = StudentVerification.objects.create(
            user=user,
            student_number="10004",
            university="UWC",
        )
        verifier = self._create_user(username="approve-publisher")

        VerifyStudentService.verify(verification, verifier)

        self.assertEqual(mock_publish.call_count, 1)
        envelope = mock_publish.call_args.args[0]
        self.assertEqual(envelope.event, EngagementEvent.STUDENT_VERIFIED)
        self.assertEqual(envelope.payload["supporter_id"], user.pk)
        self.assertEqual(envelope.payload["verification_id"], verification.pk)

    @patch("supporters.services.reject_student_verification.publish")
    def test_reject_verification_publishes_student_verification_rejected(self, mock_publish):
        user = self._create_user(username="reject-publish-user")
        verification = StudentVerification.objects.create(
            user=user,
            student_number="10005",
            university="UFS",
        )
        rejector = self._create_user(username="reject-publisher")

        RejectStudentVerificationService.reject(verification, rejected_by=rejector)

        self.assertEqual(mock_publish.call_count, 1)
        envelope = mock_publish.call_args.args[0]
        self.assertEqual(envelope.event, EngagementEvent.STUDENT_VERIFICATION_REJECTED)
        self.assertEqual(envelope.payload["supporter_id"], user.pk)
        self.assertEqual(envelope.payload["verification_id"], verification.pk)

    def test_approved_verification_removed_from_pending_queue(self):
        user = self._create_user(username="approved-queue-user")
        verifier = self._create_user(username="approved-queue-verifier")
        verification = StudentVerification.objects.create(
            user=user,
            student_number="10006",
            university="Wits",
        )

        VerifyStudentService.verify(verification, verifier)
        pending = ListPendingVerificationsService.list()

        self.assertNotIn(verification, pending)

    def test_rejected_verification_removed_from_pending_queue(self):
        user = self._create_user(username="rejected-queue-user")
        rejector = self._create_user(username="rejected-queue-rejector")
        verification = StudentVerification.objects.create(
            user=user,
            student_number="10007",
            university="NMU",
        )

        RejectStudentVerificationService.reject(verification, rejected_by=rejector)
        pending = ListPendingVerificationsService.list()

        self.assertNotIn(verification, pending)

    def test_expired_verification_allows_new_request(self):
        user = self._create_user(username="expired-request-user")
        verifier = self._create_user(username="expired-request-verifier")

        expired_verification = StudentVerification.objects.create(
            user=user,
            student_number="10008",
            university="UP",
            status=StudentVerificationStatus.VERIFIED,
            verified_at=timezone.now() - timedelta(days=400),
            expires_at=timezone.now() - timedelta(days=1),
            verified_by=verifier,
        )

        new_verification = RequestStudentVerificationService.request(
            user=user,
            student_number="10009",
            university="UP",
            requested_by=user,
        )

        self.assertEqual(new_verification.status, StudentVerificationStatus.PENDING)
        self.assertNotEqual(new_verification.pk, expired_verification.pk)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )

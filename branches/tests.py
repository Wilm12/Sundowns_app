from django.test import TestCase

from .models import Branch, BranchStatus
from .serializers import BranchSerializer


class BranchModelTests(TestCase):
    def test_branch_defaults_to_active_status(self):
        branch = Branch.objects.create(name="Test Branch")

        self.assertEqual(branch.status, BranchStatus.ACTIVE)
        self.assertIsNone(branch.branch_code)

    def test_serializer_exposes_new_branch_fields(self):
        branch = Branch.objects.create(
            name="Serializer Branch",
            branch_code="UP-TUKS",
            contact_email="branch@example.com",
            contact_phone="0123456789",
            status=BranchStatus.ACTIVE,
        )

        serializer = BranchSerializer(branch)

        self.assertEqual(serializer.data["branch_code"], "UP-TUKS")
        self.assertEqual(serializer.data["contact_email"], "branch@example.com")
        self.assertEqual(serializer.data["contact_phone"], "0123456789")
        self.assertEqual(serializer.data["status"], BranchStatus.ACTIVE)

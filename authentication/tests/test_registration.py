
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from branches.models import Branch


class RegistrationTests(APITestCase):
    def test_user_can_register_successfully(self):
        branch = Branch.objects.create(
            name="Mamelodi West",
            location="Mamelodi"
        )

        url = reverse("register")

        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "branch": branch.id,
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="testuser@example.com").exists())

        user = User.objects.get(email="testuser@example.com")

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "testuser@example.com")
        self.assertEqual(user.role, "member")
        self.assertEqual(user.branch, branch)
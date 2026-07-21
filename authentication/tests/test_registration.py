from django.contrib.auth import get_user
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from branches.models import Branch
from users.models import User


class RegistrationTests(APITestCase):
    def test_user_can_register_without_username_and_auto_generate_username(self):
        branch = Branch.objects.create(
            name="Mamelodi West",
            location="Mamelodi"
        )

        url = reverse("register")

        data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "branch": branch.id,
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="testuser@example.com").exists())

        user = User.objects.get(email="testuser@example.com")

        self.assertEqual(user.username, "testuser@example.com")
        self.assertEqual(user.email, "testuser@example.com")
        self.assertEqual(user.role, "member")
        self.assertEqual(user.branch, branch)

    def test_register_page_logs_user_in_and_redirects_to_membership_page(self):
        branch = Branch.objects.create(
            name="Mamelodi West",
            location="Mamelodi"
        )

        response = self.client.post(
            reverse("register_page"),
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "newuser@example.com",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
                "branch": branch.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("membership_page"))
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.email, "newuser@example.com")
from django.contrib.auth import get_user
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from branches.models import Branch
from users.models import User


class LoginTests(APITestCase):
    def test_user_can_login_and_receive_tokens_with_email(self):
        branch = Branch.objects.create(
            name="Johannesburg Branch",
            location="Johannesburg"
        )

        User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="StrongPass123!",
            branch=branch,
        )

        url = reverse("login")

        data = {
            "email": "testuser@example.com",
            "password": "StrongPass123!",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_web_login_uses_email_and_fails_for_wrong_password(self):
        branch = Branch.objects.create(
            name="Johannesburg Branch",
            location="Johannesburg"
        )

        user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="StrongPass123!",
            branch=branch,
        )

        response = self.client.post(
            reverse("login_page"),
            {
                "email": user.email,
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_existing_user_can_authenticate_with_email(self):
        branch = Branch.objects.create(
            name="Johannesburg Branch",
            location="Johannesburg"
        )

        user = User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="StrongPass123!",
            branch=branch,
        )

        response = self.client.post(
            reverse("login_page"),
            {
                "email": user.email,
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user(self.client).is_authenticated)
        self.assertEqual(get_user(self.client).email, user.email)

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from branches.models import Branch
from users.models import User


class LoginTests(APITestCase):
    def test_user_can_login_and_receive_tokens(self):
        branch = Branch.objects.create(
            name="Johannesburg Branch",
            location="Johannesburg"
        )

        User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123!",
            branch=branch,
        )

        url = reverse("login")

        data = {
            "username": "testuser",
            "password": "StrongPass123!",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

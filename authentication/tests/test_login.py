from django.contrib.auth import get_user
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from branches.models import Branch, BranchRole
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

    def test_branch_admin_login_redirects_to_branch_admin_dashboard(self):
        branch = Branch.objects.create(name="Cape Town Branch", location="Cape Town")
        user = User.objects.create_user(
            username="branch-admin@example.com",
            email="branch-admin@example.com",
            password="StrongPass123!",
            branch=branch,
        )
        BranchRole.objects.create(
            branch=branch,
            user=user,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        )

        response = self.client.post(
            reverse("login_page"),
            {
                "email": user.email,
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("branch_admin_dashboard"))

    def test_navigation_shows_branch_admin_link_for_authorized_users(self):
        branch = Branch.objects.create(name="Durban Branch", location="Durban")
        user = User.objects.create_user(
            username="nav-admin@example.com",
            email="nav-admin@example.com",
            password="StrongPass123!",
            branch=branch,
        )
        BranchRole.objects.create(
            branch=branch,
            user=user,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Branch Admin")
        self.assertContains(response, reverse("branch_admin_dashboard"))

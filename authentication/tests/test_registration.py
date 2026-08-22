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

    def test_register_page_logs_user_in_and_redirects_to_dashboard(self):
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
        self.assertEqual(response.url, reverse("dashboard"))
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.email, "newuser@example.com")

    def test_register_page_password_mismatch_preserves_safe_values_and_renders_error(self):
        branch = Branch.objects.create(name="Soweto Branch", location="Soweto")
        password = "StrongPass123!"
        confirmation = "DifferentPass123!"

        response = self.client.post(
            reverse("register_page"),
            {
                "first_name": "Anele",
                "last_name": "Mokoena",
                "email": "anele@example.com",
                "password": password,
                "password_confirm": confirmation,
                "branch": branch.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")
        self.assertContains(response, 'value="Anele"')
        self.assertContains(response, 'value="Mokoena"')
        self.assertContains(response, 'value="anele@example.com"')
        self.assertNotContains(response, password)
        self.assertNotContains(response, confirmation)

    def test_register_page_duplicate_email_preserves_safe_values_and_renders_error(self):
        branch = Branch.objects.create(name="Soweto Branch", location="Soweto")
        User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="StrongPass123!",
            branch=branch,
        )
        password = "AnotherPass123!"

        response = self.client.post(
            reverse("register_page"),
            {
                "first_name": "Thabo",
                "last_name": "Nkosi",
                "email": "existing@example.com",
                "password": password,
                "password_confirm": password,
                "branch": branch.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with this email already exists.")
        self.assertContains(response, 'value="Thabo"')
        self.assertContains(response, 'value="Nkosi"')
        self.assertContains(response, 'value="existing@example.com"')
        self.assertNotContains(response, password)

    def test_register_page_password_policy_error_does_not_repopulate_passwords(self):
        branch = Branch.objects.create(name="Soweto Branch", location="Soweto")
        password = "short"

        response = self.client.post(
            reverse("register_page"),
            {
                "first_name": "Lerato",
                "last_name": "Dube",
                "email": "lerato@example.com",
                "password": password,
                "password_confirm": password,
                "branch": branch.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this field has at least 8 characters.")
        self.assertContains(response, 'value="Lerato"')
        self.assertContains(response, 'value="Dube"')
        self.assertContains(response, 'value="lerato@example.com"')
        self.assertNotContains(response, password)

    def test_register_page_missing_required_field_renders_field_error(self):
        branch = Branch.objects.create(name="Soweto Branch", location="Soweto")
        password = "StrongPass123!"

        response = self.client.post(
            reverse("register_page"),
            {
                "last_name": "Maseko",
                "email": "maseko@example.com",
                "password": password,
                "password_confirm": password,
                "branch": branch.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, 'value="Maseko"')
        self.assertContains(response, 'value="maseko@example.com"')
        self.assertNotContains(response, password)

    def test_register_page_preserves_selected_branch_after_validation_failure(self):
        branch = Branch.objects.create(name="Soweto Branch", location="Soweto")
        password = "StrongPass123!"

        response = self.client.post(
            reverse("register_page"),
            {
                "first_name": "Nandi",
                "last_name": "Zulu",
                "email": "nandi@example.com",
                "password": password,
                "password_confirm": "Mismatch123!",
                "branch": branch.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<option value="{branch.id}" selected>')
        self.assertNotContains(response, password)
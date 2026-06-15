from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class AnalyticsDashboardViewTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass',
            role='admin'
        )
        self.member_user = User.objects.create_user(
            username='memberuser',
            email='member@example.com',
            password='memberpass',
            role='member'
        )

    def test_dashboard_loads_for_admin(self):
        self.client.login(username='adminuser', password='adminpass')
        response = self.client.get(reverse('analytics_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analytics/dashboard.html')
        self.assertContains(response, 'Analytics Dashboard')

    def test_non_admin_access_denied(self):
        self.client.login(username='memberuser', password='memberpass')
        response = self.client.get(reverse('analytics_dashboard'), follow=True)

        self.assertRedirects(response, reverse('dashboard'))
        self.assertContains(response, 'Only admins can access analytics.')

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from notifications.models import Notification

User = get_user_model()


class NotificationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='viewuser',
            email='view@example.com',
            password='password123'
        )

    def test_notification_list_displays_notifications(self):
        Notification.objects.create(
            user=self.user,
            title='Test notification',
            message='This is a test notification.',
            notification_type=Notification.NotificationType.SYSTEM,
        )

        self.client.login(username='viewuser', password='password123')
        response = self.client.get(reverse('notifications_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test notification')
        self.assertContains(response, 'This is a test notification.')
        self.assertContains(response, 'Unread')

    def test_notification_read_unread_behavior(self):
        Notification.objects.create(
            user=self.user,
            title='Unread notice',
            message='Unread message',
            notification_type=Notification.NotificationType.SYSTEM,
            is_read=False,
        )
        Notification.objects.create(
            user=self.user,
            title='Read notice',
            message='Read message',
            notification_type=Notification.NotificationType.SYSTEM,
            is_read=True,
        )

        self.client.login(username='viewuser', password='password123')
        response = self.client.get(reverse('notifications_list'))

        self.assertContains(response, 'Unread notice')
        self.assertContains(response, 'Read notice')
        self.assertContains(response, 'Read')
        self.assertContains(response, 'Unread')

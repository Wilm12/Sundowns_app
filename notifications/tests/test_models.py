from django.test import TestCase
from django.contrib.auth import get_user_model

from notifications.models import Notification

User = get_user_model()


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='modeluser',
            email='model@example.com',
            password='password123'
        )

    def test_notification_defaults(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Default notification',
            message='Default test message',
            notification_type=Notification.NotificationType.SYSTEM,
        )

        self.assertFalse(notification.is_read)
        self.assertEqual(notification.notification_type, 'system')
        self.assertTrue(notification.created_at is not None)

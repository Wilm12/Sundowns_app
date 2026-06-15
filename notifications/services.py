from .models import Notification


def create_notification(user, title, message, notification_type):
    """Create a notification for a user."""
    if notification_type not in Notification.NotificationType.values:
        raise ValueError(
            f'Invalid notification type: {notification_type}. '
            f'Valid types are: {list(Notification.NotificationType.values)}'
        )

    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
    )

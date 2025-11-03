from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from authentication.models import CustomUser
from .models import Notification


class NotificationModelTests(TestCase):
    def test_defaults(self):
        user = CustomUser.objects.create_user(email="user@test.com", password="pass")
        notif = Notification.objects.create(
            user=user,
            message="m",
            content_type=ContentType.objects.get_for_model(CustomUser),
            object_id=user.id,
        )
        self.assertFalse(notif.is_read)
        self.assertTrue(notif.auto_read) 
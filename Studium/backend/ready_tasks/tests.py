from django.test import TestCase
from authentication.models import CustomUser
from .models import ReadyTask


class ReadyTaskModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="owner@example.com", password="pass")

    def test_get_latest_version_returns_last(self):
        base = ReadyTask.objects.create(
            owner=self.user,
            name="Task 1",
            discipline="Math",
            type="essay",
            description="Desc",
            city="c",
            university="u",
            faculty="f",
            direction="d",
            level="l",
            tutor="t",
            price=10,
        )
        child = ReadyTask.objects.create(
            owner=self.user,
            name="Task 2",
            discipline="Math",
            type="essay",
            description="Desc",
            city="c",
            university="u",
            faculty="f",
            direction="d",
            level="l",
            tutor="t",
            price=20,
            previous_version=base,
        )
        self.assertEqual(base.get_latest_version(), child)

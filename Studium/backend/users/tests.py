from django.test import TestCase
from .models import Education


class EducationModelTests(TestCase):
    def test_default_active(self):
        edu = Education.objects.create(
            city="c",
            university="u",
            faculty="f",
            direction="d",
            level="l",
        )
        self.assertTrue(edu.active)
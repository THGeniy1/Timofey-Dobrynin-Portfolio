from django.test import TestCase
from .models import Rules


class RulesModelTests(TestCase):
    def test_create_rules(self):
        Rules.objects.create(type="rules", name="doc", path="/tmp/doc.pdf")
        self.assertEqual(Rules.objects.count(), 1)

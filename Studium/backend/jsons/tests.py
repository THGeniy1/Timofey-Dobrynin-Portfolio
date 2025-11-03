from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
from .models import JsonFile


class JsonViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.file = JsonFile.objects.create(name="test.json", path="/tmp/test.json")

    @patch("jsons.views.JsonService.get_json")
    def test_hint_view_success(self, mock_get_json):
        mock_get_json.return_value = ["a", "b"]
        res = self.client.get(reverse("get_hints", args=[self.file.name]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"jsons": ["a", "b"]})

    def test_hint_view_not_found(self):
        res = self.client.get(reverse("get_hints", args=["missing.json"]))
        self.assertEqual(res.status_code, 404) 
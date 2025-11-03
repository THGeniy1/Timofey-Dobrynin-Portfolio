from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from authentication.models import CustomUser
from feedbacks.models import Feedback
from ready_tasks.models import ReadyTask
from unittest.mock import patch


class FeedbackTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(email="owner@example.com", password="password123")
        self.user = CustomUser.objects.create_user(email="user@example.com", password="password123")
        self.task = ReadyTask.objects.create(
            owner=self.owner,
            name="Test Task",
            discipline="Math",
            type="essay",
            city="Test City",
            university="Test University",
            faculty="Test Faculty",
            direction="Test Direction",
            level="Bachelor",
            tutor="Test Tutor",
            price=100.0,
            status="review"
        )
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

    @patch("feedbacks.views.get_user_data")
    @patch("feedbacks.views.create_feedback.delay")
    def test_feedback_creation_success(self, mock_delay, mock_get_user_data):
        mock_get_user_data.return_value = self.user

        url = reverse("feedback_create")
        data = {
            "task_id": self.task.id,
            "rate": 4,
            "comment": "Очень хорошо"
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertIn("идет обработка", res.json()["message"])
        mock_delay.assert_called_once()
        args = mock_delay.call_args[1]["feedback_data"]
        self.assertEqual(float(args["rating"]), 4)
        self.assertEqual(args["user"], self.user.id)
        self.assertEqual(args["reviewer"], self.owner.id)
        self.assertEqual(args["object_id"], self.task.id)

    def test_duplicate_feedback_blocked(self):
        Feedback.objects.create(
            user=self.user,
            reviewer=self.owner,
            content_type=ContentType.objects.get_for_model(ReadyTask),
            object_id=self.task.id,
            rating=5
        )
        url = reverse("feedback_create")
        data = {
            "task_id": self.task.id,
            "rate": 3.0
        }
        res = self.client.post(url, data, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("уже оценили", res.json()["message"])

    def test_user_feedback_list(self):
        Feedback.objects.create(
            user=self.user,
            reviewer=self.owner,
            content_type=ContentType.objects.get_for_model(ReadyTask),
            object_id=self.task.id,
            rating=4,
            comment="Хорошо"
        )
        url = reverse("feedback_user", kwargs={"pk": self.owner.id})
        res = self.client.get(f"{url}?page=1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["feedback"]), 1)
        self.assertIn("has_next", res.json())

    def test_ready_task_feedback_list(self):
        Feedback.objects.create(
            user=self.user,
            reviewer=self.owner,
            content_type=ContentType.objects.get_for_model(ReadyTask),
            object_id=self.task.id,
            rating=5,
            comment="Идеально"
        )
        url = reverse("feedback_task", kwargs={"pk": self.task.id})
        res = self.client.get(f"{url}?page=1&page_size=1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["feedback"]), 1)
        self.assertIn("has_previous", res.json())

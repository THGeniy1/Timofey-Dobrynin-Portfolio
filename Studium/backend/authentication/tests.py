from django.test import TestCase
from django.urls import reverse
from authentication.models import CustomUser, Client as ClientProfile, AdminPasswordResetRequest
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone

from rest_framework.test import APIClient


class RegistrationAndLoginTests(TestCase):
    urls = 'authentication.urls'

    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        data = {
            "email": "test@example.com",
            "password": "StrongPass123",
            "name": "Имя",
            "gender": "male",
            "description": "Описание"
        }
        response = self.client.post(reverse("login"), data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.json())

    def test_login_success(self):
        CustomUser.objects.create_user(email="login@example.com", password="testpass123")
        data = {"email": "login@example.com", "password": "testpass123"}
        response = self.client.post(reverse("login"), data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())

    def test_login_invalid_password(self):
        CustomUser.objects.create_user(email="login@example.com", password="correctpass")
        data = {"email": "login@example.com", "password": "wrongpass"}
        response = self.client.post(reverse("login"), data, format="json")
        self.assertEqual(response.status_code, 401)

class PasswordResetTests(TestCase):
    urls = 'authentication.urls'

    def setUp(self):
        self.user = CustomUser.objects.create_user(email="reset@example.com", password="strongpassword")
        self.client_profile = ClientProfile.objects.create(user=self.user)
        self.reset_request = AdminPasswordResetRequest.objects.create(
            client=self.client_profile,
            token="expired-token",
        )
        old_time = timezone.now() - timedelta(hours=25)
        AdminPasswordResetRequest.objects.filter(pk=self.reset_request.pk).update(created_at=old_time)
        self.client = APIClient()

    def test_password_reset_expired(self):
        response = self.client.post(reverse("reset_password"), {
            "token": "expired-token",
            "password": "newpassword123"
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

class MeViewTests(TestCase):
    urls = 'authentication.urls'

    def setUp(self):
        self.user = CustomUser.objects.create_user(email="user@example.com", password="strongpassword")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_me_view_authenticated(self):
        response = self.client.get(reverse("user_detail"))
        self.assertEqual(response.status_code, 200)

    def test_me_view_unauthenticated(self):
        client = APIClient()
        response = client.get(reverse("user_detail"))
        self.assertEqual(response.status_code, 401)

class LogoutTests(TestCase):
    urls = 'authentication.urls'

    def setUp(self):
        self.user = CustomUser.objects.create_user(email="logout@example.com", password="logout123")
        self.refresh = RefreshToken.for_user(self.user)
        self.access = str(self.refresh.access_token)

    def test_logout_success(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
        client.cookies["refresh"] = str(self.refresh)
        response = client.post(reverse("logout"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

class TokenRefreshTests(TestCase):
    urls = 'authentication.urls'

    def setUp(self):
        self.user = CustomUser.objects.create_user(email="refresh@example.com", password="refresh123")
        self.refresh_token = str(RefreshToken.for_user(self.user))

    def test_token_refresh_success(self):
        client = APIClient()
        client.cookies["refresh"] = self.refresh_token
        response = client.post(reverse("token_refresh"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())

    def test_token_refresh_missing_cookie(self):
        response = APIClient().post(reverse("token_refresh"))
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json())

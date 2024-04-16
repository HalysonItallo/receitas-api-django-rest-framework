"""
Test for the user api
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")

User = get_user_model()


def create_user(**params):
    """Create and return a new user."""
    return User.objects.create_user(**params)


# Essa é a classe de testes para um usuário não autenticado
class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""

        payload = {
            "email": "test@example.com",
            "password": "test123pass",
            "name": "Test Name",
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists"""

        payload = {
            "email": "test@example.com",
            "password": "test123pass",
            "name": "Test Name",
        }

        create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars."""

        payload = {
            "email": "test@example.com",
            "password": "pw",
            "name": "Test Name",
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = User.objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generate token valid for credentials."""
        user_details = {
            "name": "Test name",
            "email": "test@example.com",
            "password": "test-user-password123",
        }
        create_user(**user_details)

        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test return error if credentials is invalid."""
        create_user(email="test@example.com", password="goodpass")

        # Invalid credentials
        payload = {"email": "test@example.com", "password": "badpass"}

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test  posting a blank password returns an error."""

        # Blaank password
        payload = {"email": "test@example.com", "password": ""}

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unathorizated(self):
        """Test authenticated is required for users."""

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# Essa é a classe de testes para um usuário autenticado


class PrivateUserApiTests(TestCase):
    """Test API request that require authentication."""

    def setUp(self) -> None:
        self.user = create_user(
            email="test@example.com",
            password="testpass123",
            name="Test name",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrive_profile_success(self):
        """Test retriving profile for logged in user."""

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "name": self.user.name,
                "email": self.user.email,
            },
        )

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint"""

        response = self.client.post(ME_URL, {})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""

        payload = {"name": "Update name", "password": "new_pass"}

        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password, payload["password"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

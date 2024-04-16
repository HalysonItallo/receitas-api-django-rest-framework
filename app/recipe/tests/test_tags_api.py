"""
Test for the tags API.
"""

from core.models import Tag
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

TAGS_URL = reverse("recipe:tag-list")

User = get_user_model()


def create_user(email="test@example.com", password="test123"):
    """Create and return a new user."""
    return User.objects.create_user(email=email, password=password)


class PublicTagsApiTest(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""

        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test authenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retriving a list of tags."""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        response = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer()



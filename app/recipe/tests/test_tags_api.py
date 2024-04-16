"""
Test for the tags API.
"""

from core.models import Tag
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import TagSerializer
from rest_framework import status
from rest_framework.test import APIClient

TAGS_URL = reverse("recipe:tag-list")


User = get_user_model()


def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse("recipe:tag-detail", args=[tag_id])


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
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_per_user(self):
        """Test  list of tags is limited for authenticated user."""
        user2 = create_user(email="user2@example.com")

        Tag.objects.create(user=user2, name="Fruit")
        tag = Tag.objects.create(user=self.user, name="Comfort Food")

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], tag.name)
        self.assertEqual(response.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating a tag."""

        tag = Tag.objects.create(user=self.user, name="Vegan")
        payload = {"name": "New name tag"}

        url = detail_url(tag.id)
        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()

        self.assertEqual(tag.name, payload["name"])

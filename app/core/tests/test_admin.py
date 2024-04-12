"""
Test for the django admin modifications
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class AdminSiteTests(TestCase):
    """Tests for Django admin."""

    def setUp(self) -> None:
        """Create user and client"""
        self.client = Client()
        User = get_user_model()

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="testpass123",
        )

        self.client.force_login(self.admin_user)

        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            name="Test user",
        )

    def test_users_list(self):
        """Test that users are listed on page."""
        url = reverse("admin:core_user_changelist")
        response = self.client.get(url)

        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)
        pass

    def test_edit_user_page(self):
        """Test the edit user page works."""
        url = reverse("admin:core_user_change", args=[self.user.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_user_page(self):
        """Test the create user page works."""
        url = reverse("admin:core_user_add")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

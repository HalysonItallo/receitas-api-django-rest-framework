"""
Tests for models.
"""

from decimal import Decimal

from core.models import Recipe
from django.contrib.auth import get_user_model
from django.test import TestCase


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful"""
        email = "test@example.com"
        password = "testpass123"

        User = get_user_model()

        user = User.objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalize for new users."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected_email in sample_emails:
            User = get_user_model()
            user = User.objects.create_user(email, "sample123")

            self.assertEqual(user.email, expected_email)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raise a ValueError."""

        with self.assertRaises(ValueError):
            User = get_user_model()
            User.objects.create_user("", "test123")

    def test_create_superuser(self):
        """Test creating a superuser."""
        User = get_user_model()

        user = User.objects.create_superuser("test@example.com", "test123")

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe is successful."""
        User = get_user_model()
        user = User.objects.create_user("test@example.com", "testpass123")
        recipe = Recipe.objects.create(
            user=user,
            title="Sample recipe name.",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Sample recipe description.",
        )

        self.assertEqual(str(recipe), recipe.title)

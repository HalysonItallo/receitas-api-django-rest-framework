"""
Tests for ingredient API.
"""

from decimal import Decimal

from core.models import Ingredient, Recipe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer
from recipe.tests.test_recipe_api import RECIPES_URL
from rest_framework import status
from rest_framework.test import APIClient

INGREDIENTS_URL = reverse("recipe:ingredient-list")

User = get_user_model()


def detail_url(ingredient_id):
    """Create and return an ingredient detail URL."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="test@example.com", password="testpass123"):
    """Create and return a new user."""
    return User.objects.create_user(email=email, password=password)


def create_ingredient(user, **params):
    """Create and return a new ingredient."""
    return Ingredient.objects.create(user=user, **params)


class PublicIngredientApiTests(TestCase):
    """Test unauthenticated API request."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrving ingredienst."""

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test authenticated API request."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    # Começa os testes pelas rotas de listagem

    def test_retriving_ingredients(self):
        """Test retriving a list of ingredients"""

        create_ingredient(self.user, name="Kale")
        create_ingredient(self.user, name="Vanilla")

        response = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_per_user(self):
        """Test list ingredients is limited to authenticated user."""
        user2 = create_user(email="user2@example.com")
        create_ingredient(user2, name="Salt")
        ingredient = create_ingredient(self.user, name="Pepper")

        response = self.client.get(INGREDIENTS_URL)

        # Eu testo se de fato um ingredient tá sendo apenas criado para o usário dono dele.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], ingredient.name)
        self.assertEqual(response.data[0]["id"], ingredient.id)

    # Depois rotas de atualização
    def test_update_ingredient(self):
        """Test updating an ingredient."""

        ingredient = create_ingredient(self.user, name="Cilantro")

        payload = {"name": "Coriander"}

        url = detail_url(ingredient.id)

        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()

        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""

        ingredient = create_ingredient(self.user, name="Lettuce")

        url = detail_url(ingredient.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.all()
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients to those assigned to recipes."""

        i1 = create_ingredient(user=self.user, name="Apples")
        i2 = create_ingredient(user=self.user, name="Turkey")
        recipe = Recipe.objects.create(
            title="Apple Crumble",
            time_minutes=5,
            price=Decimal("4.50"),
            user=self.user,
        )
        recipe.ingredients.add(i1)

        response = self.client.get(RECIPES_URL, {"assigned_only": 1})

        s1 = IngredientSerializer(i1)
        s2 = IngredientSerializer(i2)

        self.assertIn(s1.data, response.data)
        self.assertNotIn(s2.data, response.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique list."""

        i1 = create_ingredient(user=self.user, name="Eggs")
        Ingredient.objects.create(user=self.user, name="Lentils")
        r1 = Recipe.objects.create(
            title="Eggs Benedict",
            time_minutes=60,
            price=Decimal("7.00"),
            user=self.user,
        )

        r2 = Recipe.objects.create(
            title="Herb Eggs",
            time_minutes=20,
            price=Decimal("4.00"),
            user=self.user,
        )

        r1.ingredients.add(i1)
        r2.ingredients.add(i1)

        response = self.client.get(RECIPES_URL, {"assigned_only": 1})

        self.assertEqual(len(response.data), 1)

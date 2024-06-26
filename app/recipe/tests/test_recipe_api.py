"""
Tests for Recipe API's
"""

import os
import tempfile
from decimal import Decimal

from core.models import Ingredient, Recipe, Tag
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient

RECIPES_URL = reverse("recipe:recipe-list")
User = get_user_model()


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return an image upload URL."""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""

    defaults = {
        "title": "Sample recipe test",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf",
    }

    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return a new user."""
    return User.objects.create_user(**params)


def create_ingredient(user, **params):
    """Create and return a new ingredient."""
    return Ingredient.objects.create(user=user, **params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        response = self.client.get(RECIPES_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated  API requests."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="test123")
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """Test retriving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipe is limited to authenticated user."""
        other_user = create_user(email="other@example.com", password="test123")

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail."""

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.data, serializer.data)

    def test_create_recipe(self):
        """Testing creating a recipe."""

        payload = {
            "title": "Sample recipe test",
            "time_minutes": 30,
            "price": Decimal("5.99"),
        }

        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data["id"])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link = "https://example.com/recipe.pdf"

        recipe = create_recipe(
            user=self.user,
            title="Sample recipe test",
            link=original_link,
        )

        payload = {"title": "New Title"}
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Esse método faz com que de fato o banco seja atualizado evitando o comportamento
        # preguiçoso do django
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of a recipe."""
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe test",
            link="https://example.com/recipe.pdf",
            description="Sample recipe description",
        )

        payload = {
            "title": "New recipe test",
            "link": "https://example.com/new-recipe.pdf",
            "description": "New recipe description",
            "time_minutes": 5,
            "price": Decimal("5.26"),
        }

        url = detail_url(recipe.id)
        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        # Pega o valor do objeto e compara com o valor que tava no payload
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""

        new_user = create_user(email="user2@example.com", password="test123")
        recipe = create_recipe(self.user)

        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_recipe_other_users_recipe_error(self):
        """Test trying to delete another users recipe given error."""

        new_user = create_user(email="user2@example.com", password="test123")
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""

        payload = {
            "title": "Title a new recipe",
            "time_minutes": 30,
            "price": Decimal("4.34"),
            "tags": [
                {"name": "Vegan"},
                {"name": "Dinner"},
            ],
        }

        response = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        # Eu consigo garantir que a minha receita foi criada
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]

        self.assertEqual(recipe.tags.count(), 2)

        # verifica os nomes salvos foram os corretos e os usuários que devem ser o donos dessas tags
        for tag in payload["tags"]:
            is_exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()

            self.assertTrue(is_exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""

        tag = Tag.objects.create(user=self.user, name="Vegan")

        payload = {
            "title": "Title a new recipe",
            "time_minutes": 30,
            "price": Decimal("4.34"),
            "tags": [{"name": "Vegan"}, {"name": "Breakfast"}],
        }

        response = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())

        for tag in payload["tags"]:
            is_exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(is_exists)

    def test_create_and_update(self):
        """Test creating tag when updating a recipe."""

        recipe = create_recipe(user=self.user)

        payload = {
            "tags": [
                {"name": "Lunch"},
            ]
        }

        url = detail_url(recipe.id)

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name="Lunch")

        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assign an existing tag when updating  a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")

        payload = {
            "tags": [
                {"name": "Lunch"},
            ]
        }
        url = detail_url(recipe.id)

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags."""

        tag = Tag.objects.create(user=self.user, name="Dessert")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": []}

        url = detail_url(recipe.id)

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with new ingredients."""

        payload = {
            "title": "Title a new recipe",
            "time_minutes": 30,
            "price": Decimal("4.34"),
            "ingredients": [
                {"name": "Cauliflower"},
                {"name": "Salt"},
            ],
        }

        response = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient."""
        ingredient = create_ingredient(user=self.user, name="Lemon")

        payload = {
            "title": "Vietnamese soup",
            "time_minutes": 25,
            "price": "4.29",
            "ingredients": [
                {"name": "Lemon"},
                {"name": "Fish Sauce"},
            ],
        }

        response = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient on updating a recipe."""

        recipe = create_recipe(user=self.user)

        payload = {
            "ingredients": [
                {"name": "Limes"},
            ]
        }

        url = detail_url(recipe.id)

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(user=self.user, name="Limes")

        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe."""
        ingredient1 = create_ingredient(user=self.user, name="Pepper")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = create_ingredient(user=self.user, name="Chili")

        payload = {
            "ingredients": [
                {"name": "Chili"},
            ]
        }
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipes ingredients."""
        ingredient = create_ingredient(user=self.user, name="Garlic")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {
            "ingredients": [],
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering recipes by tags."""

        r1 = create_recipe(user=self.user, title="Thai Vegetable Curry")
        r2 = create_recipe(user=self.user, title="Aubergine with Tahini")
        tag1 = Tag.objects.create(user=self.user, name="Vegan")
        tag2 = Tag.objects.create(user=self.user, name="Vegeterian")
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title="Fish and tips")

        params = {
            "tags": f"{tag1.id},{tag2.id}",
        }

        response = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, response.data)
        self.assertIn(s2.data, response.data)
        self.assertNotIn(s3.data, response.data)

    def test_filter_by_ingredients(self):
        """Test filtering recipes by ingredients."""
        r1 = create_recipe(user=self.user, title="Thai Vegetable Curry")
        r2 = create_recipe(user=self.user, title="Aubergine with Tahini")
        i1 = create_ingredient(user=self.user, name="Feta Cheese")
        i2 = create_ingredient(user=self.user, name="Chicken")
        r1.ingredients.add(i1)
        r2.ingredients.add(i2)

        r3 = create_recipe(user=self.user, title="Red Lentil Dahl")

        params = {"ingredients": f"{i1.id},{i2.id}"}

        response = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, response.data)
        self.assertIn(s2.data, response.data)
        self.assertNotIn(s3.data, response.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user("user@example.com", "password123")
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""

        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            response = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""

        url = image_upload_url(self.recipe.id)
        payload = {"image": "notanimage"}
        response = self.client.post(url, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

"""
URL mappings for the recipe app.
"""

from django.urls import include, path
from recipe.views import RecipeViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"recipes", RecipeViewSet, basename="recipe")

app_name = "recipe"

urlpatterns = [
    path("", include(router.urls)),
]

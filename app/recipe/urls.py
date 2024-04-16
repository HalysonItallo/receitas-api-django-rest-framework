"""
URL mappings for the recipe app.
"""

from django.urls import include, path
from recipe.views import RecipeViewSet, TagViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"recipes", RecipeViewSet, basename="recipe")
router.register(r"tags", TagViewSet, basename="tag")

app_name = "recipe"

urlpatterns = [
    path("", include(router.urls)),
]

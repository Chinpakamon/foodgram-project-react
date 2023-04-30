from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet
from .views import TagViewSet, RecipesViewSet, IngredientsViewSet, ShoppingCartView

v1_router = DefaultRouter()
v1_router.register('users', UserViewSet, basename='user')
v1_router.register('tags', TagViewSet, basename='tag')
v1_router.register('recipes', RecipesViewSet, basename='recipes')
v1_router.register('ingredients', IngredientsViewSet, basename='ingredients')


urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/download_shopping_cart/', ShoppingCartView.as_view())
]
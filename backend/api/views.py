from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Favorite, Ingredient, IngredientQuantity, Recipe,
                            ShoppingCart, Tag)
from users.models import User

from .filters import IngredientsFilter, RecipesFilter
from .mixins import ViewSetMixin
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (GetRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeSubscribeSerializer,
                          TagSerializer)


class TagViewSet(ViewSetMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(ViewSetMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientsFilter
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    filterset_class = RecipesFilter
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_favorited is not None and int(is_favorited) == 1:
            return Recipe.objects.filter(is_favorited=self.request.user)
        elif is_in_shopping_cart is not None and int(is_in_shopping_cart) == 1:
            return Recipe.objects.filter(is_in_shopping_cart=self.request.user)
        return Recipe.objects.all()

    def get_permissions(self):
        if self.action in ('partial_update', 'destroy'):
            return IsAuthorOrReadOnly
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == ['GET']:
            return GetRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        data = self.get_object()
        self.perform_destroy(data)
        return Response({"message": "You deleted the recipe"},
                        status=status.HTTP_204_NO_CONTENT)

    def post_delete(self, request, pk, model, serializer):
        if self.request.method == 'POST':
            recipes = get_object_or_404(Recipe, pk=pk)
            if model.objects.filter(user=request.user,
                                    recipes=recipes).exists():
                return Response(
                    {"message": "Recipe already in favorites/Shopping List"},
                    status=status.HTTP_400_BAD_REQUEST)
            model.objects.get_or_create(user=request.user, recipes=recipes)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipes = get_object_or_404(Recipe, pk=pk)
        if model.objects.filter(user=request.user, recipes=recipes).exists():
            get_object_or_404(model, user=request.user,
                              recipes=recipes).delete()
            return Response({"message": "Recipe removed"},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "Recipe not in favorites/Shopping List"},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST', 'DELETE'])
    def is_favorited(self, request, pk):
        model = Favorite
        serializer = RecipeSubscribeSerializer
        return self.post_delete(request, pk, model, serializer)

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk):
        model = ShoppingCart
        serializer = RecipeSubscribeSerializer
        return self.post_delete(request, pk, model, serializer)


class ShoppingCartView(APIView):
    @action(methods=['GET'], detail=False, url_path='download_shopping_cart',
            permission_classes=[permissions.IsAuthenticated])
    def get(self, request):
        ingredients = IngredientQuantity.objects.filter(
            cart_user=self.request.user).values('ingredient__name',
                                                'ingredient__measurement_unit').ordered_by(
            'ingredient_name').annotate(amount=Sum('quantity'))
        user = get_object_or_404(User, username=request.user)
        filename = f'{user.username}_shopping_list.txt'
        now = timezone.now()
        shopping_list = (
            f'Список покупок для пользователя: {user.username}\n\n'
            f'Дата: {now:%Y-%m-%d}\n\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({now:%Y})'
        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

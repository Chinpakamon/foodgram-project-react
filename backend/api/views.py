from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientQuantity, Recipe,
                            ShoppingCart, Tag)

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


class IngredientViewSet(ViewSetMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientsFilter
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filterset_class = RecipesFilter
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_favorited is not None and int(is_favorited) == 1:
            return Recipe.objects.filter(favorites__user=self.request.user)
        if is_in_shopping_cart is not None and int(is_in_shopping_cart) == 1:
            return Recipe.objects.filter(cart__user=self.request.user)
        return Recipe.objects.all()

    def get_permissions(self):
        if self.action != 'create':
            return (IsAuthorOrReadOnly(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return GetRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return Response({"message": "You deleted the recipe"},
                        status=status.HTTP_204_NO_CONTENT)

    def post_delete(self, request, pk, model, serializer):
        if self.request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)
            if model.objects.filter(user=request.user,
                                    recipe=recipe).exists():
                return Response(
                    {"message": "Recipe already in favorites/Shopping List"},
                    status=status.HTTP_400_BAD_REQUEST)
            model.objects.get_or_create(user=request.user, recipe=recipe)
            return Response(serializer(recipe).data,
                            status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            if model.objects.filter(user=request.user,
                                    recipe=recipe).exists():
                data = get_object_or_404(model, user=request.user,
                                         recipe=recipe)
                data.delete()
                return Response({"message": "Recipe/Cart removed"},
                                status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"message": "Recipe not in favorites/Shopping List"},
                status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk):
        model = Favorite
        serializer = RecipeSubscribeSerializer
        return self.post_delete(request, pk, model, serializer)

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk):
        model = ShoppingCart
        serializer = RecipeSubscribeSerializer
        return self.post_delete(request, pk, model, serializer)

    @action(detail=False, methods=('GET',),
            permission_classes=[permissions.IsAuthenticated, ])
    def download_shopping_cart(self, request):
        user = request.user
        filename = f'{user.username}_shopping_list.txt'
        now = timezone.now()
        shopping_list = [
            f'Список покупок для пользователя: {user.username}\n\n'
            f'Дата: {now:%Y-%m-%d}\n\n'
        ]
        ingredients = IngredientQuantity.objects.filter(
            recipe__cart__user=user).values('ingredient__name',
                                            'ingredient__measurement_unit'
                                            ).annotate(
            ingredient_amount=Sum('amount'))

        for ing in ingredients:
            shopping_list.append(
                f'{ing["ingredient__name"]}: {ing["ingredient_amount"]} '
                f'{ing["ingredient__measurement_unit"]}'
            )
        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

from django.utils import timezone

from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import Tag, Recipe, Ingredient, ShoppingCart, Favorite, IngredientQuantity
from users.models import User
from .pagination import CustomPagination
from .mixins import ViewSetMixin
from .permissions import IsAuthorOrReadOnly
from .filters import IngredientsFilter, RecipesFilter
from .serializers import (TagSerializer, RecipeSerializer, IngredientSerializer, RecipeSubscribeSerializer,
                          GetRecipeSerializer)


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
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
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
        return Response({"message": "You deleted the recipe"}, status=status.HTTP_204_NO_CONTENT)

    def post_delet(self, request, pk, model, serializer):
        if self.request.method == 'POST':
            recipes = get_object_or_404(Recipe, pk=pk)
            if model.objects.filter(user=request.user, recipes=recipes).exists():
                return Response({"message": "Recipe already in favorites/Shopping List"},
                                status=status.HTTP_400_BAD_REQUEST)
            model.objects.get_or_create(user=request.user, recipes=recipes)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipes = get_object_or_404(Recipe, pk=pk)
        if model.objects.filter(user=request.user, recipes=recipes).exists():
            get_object_or_404(model, user=request.user, recipes=recipes).delete()
            return Response({"message": "Recipe removed"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "Recipe not in favorites/Shopping List"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST', 'DELETE'])
    def is_favorited(self, request, pk):
        model = Favorite
        serializer = RecipeSubscribeSerializer
        return self.post_delet(request, pk, model, serializer)

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk):
        model = ShoppingCart
        serializer = RecipeSubscribeSerializer
        return self.post_delet(request, pk, model, serializer)


class ShoppingCartView(APIView):
    @action(methods=['GET'], detail=False, url_path='download_shopping_cart')
    def get(self, request):
        user = get_object_or_404(User, username=request.user)
        shopping_list = ShoppingCart.objects.filter(user=user).values('recipes')
        recipes = Recipe.objects.filter(pk__in=shopping_list)
        shop_list: dict = {}
        n_rec = 0
        for recipe in recipes:
            n_rec += 1
            ing_quantity = IngredientQuantity.objects.filter(recipes=recipe)
            for i in ing_quantity:
                if i.ingredients.name in shop_list:
                    shop_list[i.ingredients.name][0] += i.quantity
                else:
                    shop_list[i.ingredients.name] = [i.quantity, i.ingredients.measurement_unit]
        now = timezone.now()
        now = now.strftime("%d-%m-%Y")
        shop_string = (
            f'FoodGram\nВыбрано рецептов: {n_rec}\
                    \n-------------------\n{now}\
                    \nСписок покупок:\
                    \n-------------------'
        )

        for key, value in shop_list.items():
            shop_string += f'\n{key} ({value[1]}) - {str(value[0])}'
        return HttpResponse(shop_string, content_type='text/plain')

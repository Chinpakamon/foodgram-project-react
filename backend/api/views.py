import datetime

from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from recipes.models import Tag, Recipes, Ingredients, ShoppingCart, Favorite, IngredientsQuantity

from users.models import User
from .pagination import CustomPagination
from .mixins import ViewSetMixin
from .permissions import IsAuthorOrReadOnly
from .filters import IngredientsFilter, RecipesFilter
from .serializers import TagSerializer, RecipesSerializer, IngredientsSerializer, RecipesSubscribeSerializer, \
    GetRecipesSerializer


class TagViewSet(ViewSetMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientsViewSet(ViewSetMixin):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    filterset_class = IngredientsFilter
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipesSerializer
    pagination_class = CustomPagination
    filterset_class = RecipesFilter
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_favorited is not None and int(is_favorited) == 1:
            return Recipes.objects.filter(is_favorited=self.request.user)
        elif is_in_shopping_cart is not None and int(is_in_shopping_cart) == 1:
            return Recipes.objects.filter(is_in_shopping_cart=self.request.user)
        else:
            return Recipes.objects.all()

    def get_permissions(self):
        if self.action in ('partial_update', 'destroy'):
            return IsAuthorOrReadOnly
        else:
            return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == ['GET']:
            return GetRecipesSerializer
        else:
            return RecipesSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        data = self.get_object()
        self.perform_destroy(data)
        return Response({"message": "You deleted the recipe"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST', 'DELETE'])
    def is_favorited(self, request, pk):
        model = Favorite
        serializer = RecipesSubscribeSerializer
        if self.request.method == 'POST':
            recipes = get_object_or_404(Recipes, pk=pk)
            if model.objects.filter(user=request.user, recipes=recipes).exists():
                return Response({"message": "Recipe already in favorites"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                model.objects.get_or_create(user=request.user, recipes=recipes)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            recipes = get_object_or_404(Recipes, pk=pk)
            if model.objects.filter(user=request.user, recipes=recipes).exists():
                get_object_or_404(model, user=request.user, recipes=recipes).delete()
                return Response({"message": "Recipe removed"}, status=status.HTTP_204_NO_CONTENT)
            return Response({"message": "Recipe not in favorites"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk):
        model = ShoppingCart
        serializer = RecipesSubscribeSerializer
        if self.request.method == 'POST':
            recipes = get_object_or_404(Recipes, pk=pk)
            if model.objects.filter(user=request.user, recipes=recipes).exists():
                return Response({"message": "Recipe already in Shopping List"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                model.objects.get_or_create(user=request.user, recipes=recipes)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            recipes = get_object_or_404(Recipes, pk=pk)
            if model.objects.filter(user=request.user, recipes=recipes).exists():
                get_object_or_404(model, user=request.user, recipes=recipes).delete()
                return Response({"message": "Recipe removed"}, status=status.HTTP_204_NO_CONTENT)
            return Response({"message": "Recipe not in Shopping List"}, status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartView(APIView):
    @action(methods=['GET'], detail=False, url_path='download_shopping_cart')
    def get(self, request):
        user = get_object_or_404(User, username=request.user)
        shopping_list = ShoppingCart.objects.filter(user=user).values('recipes')
        recipes = Recipes.objects.filter(pk__in=shopping_list)
        shop_dict = {}
        n_rec = 0
        for recipe in recipes:
            n_rec += 1
            ing_quantity = IngredientsQuantity.objects.filter(recipes=recipe)
            for i in ing_quantity:
                if i.ingredients.name in shop_dict:
                    shop_dict[i.ingredients.name][0] += i.quantity
                else:
                    shop_dict[i.ingredients.name] = [i.quantity, i.ingredients.measurement_unit]
        now = datetime.datetime.now()
        now = now.strftime("%d-%m-%Y")
        shop_string = (
            f'FoodGram\nВыбрано рецептов: {n_rec}\
                    \n-------------------\n{now}\
                    \nСписок покупок:\
                    \n-------------------'
        )

        for key, value in shop_dict.items():
            shop_string += f'\n{key} ({value[1]}) - {str(value[0])}'
        return HttpResponse(shop_string, content_type='text/plain')

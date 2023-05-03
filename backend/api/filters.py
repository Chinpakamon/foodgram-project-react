import django_filters
from django.contrib.auth import get_user_model

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class RecipesFilter(django_filters.FilterSet):
    tag = django_filters.ModelMultipleChoiceFilter(field_name='tag',
                                                   queryset=Tag.objects.all())
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = Recipe
        fields = ('tag', 'author')

from django.contrib.auth import get_user_model
import django_filters

from recipes.models import Tag, Ingredients, Recipes

User = get_user_model()


class IngredientsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredients
        fields = ('name', 'measurement_unit')


class RecipesFilter(django_filters.FilterSet):
    tag = django_filters.ModelMultipleChoiceFilter(field_name='tag', queryset=Tag.objects.all())
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = Recipes
        fields = ('tag', 'author')

from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientQuantity, Recipe,
                     ShoppingCart, Tag)


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name', 'measurement_unit')
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'author', 'text', 'cooking_time', 'pub_date',
        'count_favor')
    list_filter = ('author', 'name', 'tag')
    search_fields = ('author', 'name', 'tag', 'ingredients', 'cooking_time')
    empty_value_display = '-пусто-'

    def count_favor(self, obj):
        return obj.is_favorited.count()


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipes')
    list_filter = ('user', 'recipes')
    search_fields = ('user', 'recipes')
    empty_value_display = '-пусто-'


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipes')
    list_filter = ('user', 'recipes')
    search_fields = ('user', 'recipes')
    empty_value_display = '-пусто-'


class IngredientQuantityAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipes', 'quantity', 'ingredients')
    search_fields = ('recipes', 'ingredients',)
    list_filter = ('recipes', 'ingredients',)
    empty_value_display = '-пусто-'


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(IngredientQuantity, IngredientQuantityAdmin)

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField('Название ингредиента', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    class Meta:
        ordering = ['name', ]
        verbose_name = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}({self.measurement_unit})'


class Tag(models.Model):
    name = models.CharField('Название тега', max_length=200, unique=True)
    color = models.CharField('Цвет', max_length=7, unique=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['name', ]
        verbose_name = 'Тег'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор публикации',
                               related_name='recipe_author')
    name = models.CharField('Название', max_length=200)
    image = models.ImageField('Картинка', )
    text = models.TextField('Текстовое описание', )
    ingredients = models.ManyToManyField(Ingredient, verbose_name='Ингредиенты', )
    tag = models.ManyToManyField(Tag, verbose_name='Тег')
    cooking_time = models.PositiveIntegerField(verbose_name='Время приготовления в минутах',
                                               validators=[MinValueValidator(1)])
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-pub_date', ]
        verbose_name = 'Рецепт'

    def __str__(self):
        return f'Рецепт {self.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='is_in_shopping_cart',
                             on_delete=models.CASCADE)
    recipes = models.ForeignKey(Recipe, verbose_name='Рецепт', related_name='is_in_shopping_cart',
                                on_delete=models.CASCADE)

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Добавление рецепта в список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='shopping_user_recipes'
            )
        ]

    def __str__(self):
        return f'{self.user}, {self.recipes}'


class Favorite(models.Model):
    recipes = models.ForeignKey(Recipe, verbose_name='Избранный рецепт', related_name='is_favorited',
                                on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='is_favorited', on_delete=models.CASCADE)

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Добавление рецепта в избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='unique_user_recipes'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} добавил {self.recipes} в избранное'


class IngredientQuantity(models.Model):
    recipes = models.ForeignKey(Recipe, verbose_name='Рецепт', related_name='recipes', on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(verbose_name='Количество ингредиента',
                                                validators=[MinValueValidator(1)])
    ingredients = models.ForeignKey(Ingredient, verbose_name='Ингридиент', related_name='ingredients',
                                    on_delete=models.CASCADE)

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Количество ингредиента'
        constraints = [
            models.UniqueConstraint(
                fields=['recipes', 'ingredients'],
                name='recipes_ingredient',
            )
        ]

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField('Название ингредиента', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    class Meta:
        ordering = ('name', )
        verbose_name = 'Ингредиент'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('Название тега', max_length=200, unique=True)
    color = models.CharField('Цвет', max_length=7, unique=True,
                             default='#FF0000')
    slug = models.SlugField('slug', max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор публикации',
                               related_name='recipes')
    name = models.CharField('Название', max_length=200)
    image = models.ImageField('Картинка', )
    text = models.TextField('Текстовое описание', )
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингредиенты',
                                         through='IngredientQuantity')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[MinValueValidator(1)],)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True,
                                    db_index=True)

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Рецепт'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_author_name'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='cart',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, verbose_name='Список рецептов',
                               related_name='cart',
                               on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Добавление рецепта в список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='shopping_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user}, {self.recipe}'


class Favorite(models.Model):
    recipe = models.ForeignKey(Recipe, verbose_name='Избранный рецепт',
                               related_name='favorites',
                               on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='favorites',
                             on_delete=models.CASCADE)

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Добавление рецепта в избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'Пользователь {self.user} добавил {self.recipe} в избранное'


class IngredientQuantity(models.Model):
    recipe = models.ForeignKey(Recipe, verbose_name='Рецепт',
                               related_name='amount',
                               on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=[MinValueValidator(1)])
    ingredient = models.ForeignKey(Ingredient, verbose_name='Ингридиент',
                                   related_name='amount',
                                   on_delete=models.CASCADE)

    class Meta:
        ordering = ('-id', )
        verbose_name = 'Количество ингредиента'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipes_ingredient',
            )
        ]

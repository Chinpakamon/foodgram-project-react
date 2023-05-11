from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Ingredient, IngredientQuantity, Recipe, Tag
from users.models import Subscription
from users.serializers import UserListSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class GetIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientQuantity
        fields = ('id', 'name', 'measurement_unit', 'quantity')
        validators = [
            UniqueTogetherValidator(queryset=IngredientQuantity.objects.all(),
                                    fields=['ingredient', 'recipe'])
        ]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    quantity = serializers.IntegerField(write_only=True, min_value=1)
    id = serializers.PrimaryKeyRelatedField(source='ingredient',
                                            queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientQuantity
        fields = ('id', 'recipe', 'quantity')


class RecipeSubscribeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')

    class Meta:
        model = Subscription
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(user=obj.user,
                                           author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeSubscribeSerializer(queryset, many=True).data


class GetRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserListSerializer(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'tags', 'ingredients', 'is_in_shopping_cart',
                  'is_favorited', 'image', 'name', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorites.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.cart.filter(user=user).exists()
        return False

    def get_ingredients(self, obj):
        recipe_ingredients = IngredientQuantity.objects.filter(recipe=obj)
        return GetIngredientSerializer(recipe_ingredients,
                                       many=True).data


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    author = UserListSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True)
    cooking_time = serializers.IntegerField(min_value=1)
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'tags', 'ingredients', 'image', 'name', 'text',
            'cooking_time')

    def create_update(self, datas, model, recipe):
        create_data = (model(recipe=recipe, ingredient=data['ingredient'],
                             quantity=data['quantity']) for data in datas)
        model.objects.bulk_create(create_data)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_update(ingredients_data, IngredientQuantity, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in self.validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)
        if 'ingredients' in self.validated_data:
            ingredients_data = validated_data.pop('ingredients')
            quantity = IngredientQuantity.objects.filter(
                recipe_id=instance.id)
            quantity.delete()
            self.create_update(ingredients_data, IngredientQuantity, instance)
        return super().update(instance, validated_data)

    def represent(self, instance):
        self.fields.pop('ingredients')
        self.fields.pop('tags')
        represent = super().to_representation(instance)
        represent['ingredients'] = GetIngredientSerializer(
            IngredientQuantity.objects.filter(recipe=instance),
            many=True).data
        represent['tags'] = TagSerializer(instance.tags, many=True).data
        return represent

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = [ingredient['id'] for ingredient in ingredients]
        if len(ingredients_list) != len(set(ingredients_list)):
            raise serializers.ValidationError(
                'Which ingredient is listed more than once')
        return data

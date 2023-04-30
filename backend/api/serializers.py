from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from drf_extra_fields.fields import Base64ImageField

from users.models import Subscriptions
from users.serializers import UserListSerializer
from recipes.models import Tag, Recipes, Ingredients, IngredientsQuantity

User = get_user_model()


class TagSerializer(serializers.Serializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.Serializer):
    class Meta:
        model = Ingredients
        fields = '__all__'


class GetIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True, source='ingredients', slug_field='name')
    name = serializers.SlugRelatedField(read_only=True, source='ingredients')
    measurement_unit = serializers.SlugRelatedField(read_only=True, source='ingredients', slug_field='measurement_unit')

    class Meta:
        model = IngredientsQuantity
        fields = ('pk', 'name', 'measurement_unit', 'quantity')
        validators = [
            UniqueTogetherValidator(queryset=IngredientsQuantity.objects.all(),
                                    fields=['ingredients', 'recipes'])
        ]


class RecipesIngredientsSerializer(serializers.ModelSerializer):
    recipes = serializers.PrimaryKeyRelatedField(read_only=True)
    quantity = serializers.IntegerField(write_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredients',
        queryset=Ingredients.objects.all()
    )

    class Meta:
        model = IngredientsQuantity
        fields = ('pk', 'recipes', 'quantity')


class RecipesSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = ('pk', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')

    class Meta:
        model = Subscriptions
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        return Subscriptions.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipes.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipesSubscribeSerializer(queryset, many=True).data


class GetRecipesSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserListSerializer(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipes
        fields = ('pk', 'author', 'tags', 'ingredients', 'is_in_shopping_cart', 'is_favorited', 'image', 'name', 'text',
                  'cooking_time')

    def get_ingredients(self, obj):
        ingredients = IngredientsQuantity.objects.filter(recipes=obj)
        return RecipesIngredientsSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.is_favorited.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.is_in_shopping_cart.filter(user=user).exists()


class RecipesSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    author = UserListSerializer(read_only=True)
    ingredients = RecipesIngredientsSerializer(many=True)
    cooking_time = serializers.IntegerField(min_value=1)
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipes
        fields = ('pk', 'author', 'tags', 'ingredients', 'image', 'name', 'text',
                  'cooking_time')

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipes = Recipes.objects.create(**validated_data)
        recipes.tag.set(tags_data)
        create_data = (IngredientsQuantity(recipes=recipes, ingredients=ingredients_data['ingredients'],
                                           quantity=ingredients_data['quantity']) for i in ingredients_data)
        IngredientsQuantity.objects.bulk_create(create_data)
        return recipes

    def update(self, instance, validated_data):
        if 'tag' in self.validated_data:
            tags_data = validated_data.pop('tags')
            instance.tag.set(tags_data)
        if 'ingredients' in self.validated_data:
            ingredients_data = validated_data.pop('ingredients')
            quantity = IngredientsQuantity.objects.filter(recipes_id=instance.id)
            quantity.delete()
            create_data = (IngredientsQuantity(recipes=instance, ingredients=ingredients_data['ingredients'],
                                               quantity=ingredients_data['quantity']) for i in ingredients_data)
            IngredientsQuantity.objects.bulk_create(create_data)
            return super().update(instance, validated_data)

    def represent(self, instance):
        self.fields.pop('ingredients')
        self.fields.pop('tags')
        represent = super().to_representation(instance)
        represent['ingredients'] = GetIngredientsSerializer(IngredientsQuantity.objects.filter(recipes=instance),
                                                            many=True).data
        represent['tags'] = TagSerializer(instance.tag, many=True).data
        return represent

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = [ingredient['id'] for ingredient in ingredients]
        if len(ingredients_list) != len(set(ingredients_list)):
            return serializers.ValidationError('Which ingredient is listed more than once')
        return data

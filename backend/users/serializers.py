from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from .models import Subscription

User = get_user_model()


class CreateUserSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')


class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

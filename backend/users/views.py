from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.serializers import SubscriptionSerializer
from .models import Subscription

User = get_user_model()


class UserViewSet(UserViewSet):
    pagination_class = CustomPagination

    @action(detail=True, permission_classes=[permissions.IsAuthenticated],
            methods=['POST', 'DELETE'])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        sub = Subscription.objects.filter(author=author, user=user)
        if self.request.method == 'POST':
            if user == author:
                return Response({'message': 'You can`t subscribe to yourself'},
                                status=status.HTTP_400_BAD_REQUEST)
            if sub.exists():
                return Response({'message': 'You are already subscribed'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscriptionSerializer(
                Subscription.objects.create(user=user, author=author),
                context={'request': request}).data
            return Response(serializer, status=status.HTTP_201_CREATED)
        if sub.exists():
            obj = get_object_or_404(Subscription, user=user,
                                    author=author)
            obj.delete()
            return Response({'message': 'You unsubscribed'},
                            status=status.HTTP_204_NO_CONTENT)
        if user == author:
            return Response({'message': 'You can`t unfollow yourself'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'You are not subscribed'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[permissions.IsAuthenticated],
            methods=['GET'])
    def subscriptions(self, request):
        queryset = self.paginate_queryset(
            Subscription.objects.filter(user=request.user))
        serializer = SubscriptionSerializer(queryset, many=True,
                                            context={'request': request}).data
        return self.get_paginated_response(serializer)

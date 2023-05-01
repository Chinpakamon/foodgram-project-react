from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers import SubscriptionSerializer
from .models import Subscription

User = get_user_model()


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, permission_classes=[permissions.IsAuthenticated], methods=['POST', 'DELETE'])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        sub = Subscription.objects.filter(author=author, user=user)
        if self.request.method == 'POST':
            if user == author:
                return Response({"message": "You can't subscribe to yourself"}, status=status.HTTP_400_BAD_REQUEST)
            if sub.exists():
                return Response({"message": "You are already subscribed"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = SubscriptionSerializer(Subscription.objects.create(user=user, author=author),
                                                     context={'request': request})
                return Response({"message": "You are now subscribed"}, serializer.data,
                                status=status.HTTP_201_CREATED)
        if Subscription.objects.filter(user=user, author=author).exists():
            subscribe = get_object_or_404(SubscriptionSerializer, user=user, author=author)
            subscribe.delete()
            return Response({"message": "You unsubscribed"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "You are not subscribed"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, permission_classes=[permissions.IsAuthenticated], methods=['GET'])
    def subscriptions(self, request):
        user = request.user
        queryset = self.paginate_queryset(Subscription.objects.filter(user=user))
        serializer = SubscriptionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

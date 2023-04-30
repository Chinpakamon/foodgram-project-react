from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField('Адрес электронной почты', max_length=254, unique=True)
    username = models.CharField('Уникальный юзернейм', max_length=150, unique=True)
    first_name = models.CharField('Имя', max_length=150, )
    last_name = models.CharField('Фамилия', max_length=150)
    password = models.CharField('Пароль', max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'username'],
                name='unique_user'
            )
        ]

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор', related_name='author', on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name='Подписчик', related_name='follower', on_delete=models.CASCADE)

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Подписка'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

from django.contrib.auth import get_user_model
from django.db import models

from core.models import DateAbstractModel

User = get_user_model()


class Post(DateAbstractModel):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(
        'Название группы',
        help_text='Введите название группы',
        max_length=200
    )
    slug = models.SlugField(
        'Адрес для группы',
        unique=True,
        help_text=(
            'Укажите уникальный адрес для группы. '
            'Используйте только латиницу, цифры, '
            'дефисы и знаки подчёркивания'
        )
    )
    description = models.TextField(
        'Описание группы',
        help_text='Введите описание группы',
    )

    def __str__(self):
        return self.title


class Comment(DateAbstractModel):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        related_name='comments'
    )
    text = models.TextField('Комментарий', max_length=200)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор канала',
        related_name='following'
    )

    def __str__(self):
        return f'Пользователь "{self.user}" подписан на "{self.author}"'

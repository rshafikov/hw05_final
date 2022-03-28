from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        test_models_expect = {
            'Тестовый пост': post,
            'Тестовая группа': group,
        }
        for expect, model in test_models_expect.items():
            with self.subTest(field=expect):
                self.assertEqual(str(model), expect)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        group = PostModelTest.group
        models = {
            post: {
                'text': 'Текст поста',
                'created': 'Дата публикации',
                'author': 'Автор',
                'group': 'Группа',
            },
            group: {
                'title': 'Название группы',
                'slug': 'Адрес для группы',
                'description': 'Описание группы',
            },
        }
        for model in models:
            for field, expect in models[model].items():
                with self.subTest(field=field):
                    self.assertEqual(
                        model._meta.get_field(field).verbose_name, expect)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        group = PostModelTest.group
        models = {
            post: {
                'text': 'Введите текст поста',
                'group': 'Группа, к которой будет относиться пост',
            },
            group: {
                'title': 'Введите название группы',
                'slug': 'Укажите уникальный адрес для группы. '
                        'Используйте только латиницу, цифры, '
                        'дефисы и знаки подчёркивания',
                'description': 'Введите описание группы',
            },
        }
        for model in models:
            for field, expect in models[model].items():
                with self.subTest(field=field):
                    self.assertEqual(
                        model._meta.get_field(field).help_text, expect)

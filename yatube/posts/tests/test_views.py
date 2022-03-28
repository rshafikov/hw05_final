import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        Group.objects.create(
            title='test group',
            slug='slug',
            description='description',
        )
        for i in range(17):
            Post.objects.create(
                text=f'Текст поста #{i + 1}',
                author=cls.user,
                group=Group.objects.get(id=1),
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTests.user)

    def test_views_use_correct_template(self):
        """View-функциию используют соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'slug'}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'HasNoName'}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}
                    ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_contains_correct_context_list(self):
        """Контекст шаблона index содержит корректный context."""
        expect_title = 'Последние обновления на сайте'
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        context = list(response.context['page_obj'].object_list)
        paginator = Paginator(Post.objects.order_by('-created'), 10)
        expect_list = list(paginator.get_page(1).object_list)
        self.assertEqual(context, expect_list)
        self.assertEqual(response.context['title'], expect_title)

    def test_group_list_page_contains_correct_context_list(self):
        """View-функция group_list содержит в контексте список постов """
        """отфильтрованных по группе и корректный title."""
        slug = 'slug'
        expect_group = Group.objects.get(slug='slug', id=1)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': slug})
        )
        context = response.context['page_obj'].object_list
        group = Group.objects.get(slug=slug)
        paginator = Paginator(group.posts.order_by('-created'), 10)
        expect_list = list(paginator.get_page(1).object_list)
        self.assertEqual(context, expect_list)
        self.assertEqual(response.context['group'], expect_group)

    def test_profile_page_contains_correct_context_list(self):
        """View-функция profile содержит в контексте список """
        """постов отфильтрованных по пользователю и author."""
        username = 'HasNoName'
        expect_author = User.objects.get(username=username)
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': username})
        )
        context = response.context['page_obj'].object_list
        user = User.objects.get(username=username)
        paginator = Paginator(user.posts.order_by('-created'), 10)
        expect_list = list(paginator.get_page(1).object_list)
        self.assertEqual(context, expect_list)
        self.assertEqual(response.context['author'], expect_author)

    def test_post_detail_page_context(self):
        """В профиль пользователя выводится корретный пост """
        """и счетчик постов у пользователя."""
        post_id = 1
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        post = response.context['post']
        expect = Post.objects.get(id=post_id)
        expect_post_count = expect.author.posts.count()
        self.assertEqual(post, expect)
        self.assertEqual(response.context['post_count'], expect_post_count)

    def test_post_edit_uses_correct_form(self):
        """Форма редактирования поста корректна."""
        post_id = 1
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context['is_edit'])

    def test_post_create_uses_correct_form(self):
        """Форма создания поста корректна."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_contains_correct_context(self):
        """Доп. проверка страниц на содержание указанного поста."""
        pages_for_test = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
            reverse('posts:group_list', kwargs={'slug': 'slug'})
        ]
        for page in pages_for_test:
            response = self.authorized_client.get(page)
            first_object = response.context['page_obj'][0]
            fields_to_test = {
                first_object.text: 'Текст поста #17',
                first_object.author.username: 'HasNoName',
                first_object.group.title: 'test group',
            }
            for field, expect in fields_to_test.items():
                with self.subTest(field=field):
                    self.assertEqual(field, expect)

    def test_first_page_contains_ten_records(self):
        pages_for_test = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
            reverse('posts:group_list', kwargs={'slug': 'slug'})
        ]
        for page in pages_for_test:
            response = self.client.get(page)
            self.assertEqual(response.context['page_obj'].end_index(), 10)

    def test_second_page_contains_eight_records(self):
        pages_for_test = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
            reverse('posts:group_list', kwargs={'slug': 'slug'})
        ]
        for page in pages_for_test:
            response = self.client.get(page + '?page=2')
            self.assertEqual(response.context['page_obj'].end_index(), 17)

    def test_image_exists_in_every_desired_location(self):
        """Изображение передается в контекст необходимых страниц"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'test text',
            'group': Group.objects.get(pk=1).pk,
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        test_urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'slug'}),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
            reverse('posts:post_detail', kwargs={'post_id': 18})
        ]
        for url in test_urls:
            context = self.authorized_client.get(url).context
            if context.get('page_obj'):
                self.assertEqual(
                    context['page_obj'].object_list[0].image,
                    'posts/small.gif'
                )
            else:
                self.assertEqual(context['post'].image, 'posts/small.gif')

    def test_comment_exists_at_desired_location_after_create(self):
        """После успешной отправки комментарий появляется на странице поста"""
        test_post = Post.objects.get(id=1)
        comment_counter = test_post.comments.count()
        form_data = {'text': 'just a simple comment'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': test_post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(test_post.comments.count(), comment_counter + 1)
        comment_text = response.context['comments'][0].text
        self.assertEqual(comment_text, 'just a simple comment')

    def test_cache(self):
        test_post = Post.objects.create(
            text='test',
            author=PostsViewsTests.user
        )
        cached_index = self.client.get(reverse('posts:index')).content
        test_post.delete()
        self.assertEqual(
            cached_index,
            self.client.get(reverse('posts:index')).content
        )
        cache.clear()
        self.assertNotEqual(
            cached_index,
            self.client.get(reverse('posts:index')).content
        )


class PostsFollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user_1')
        cls.author = User.objects.create_user(username='test_author_1')
        cls.group = Group.objects.create(
            title='test group',
            slug='slug',
            description='description',
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.guest = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsFollowTests.user)

    def test_follow_users_for_authorized_client(self):
        """Авторизованный пользователь может подписываться """
        """на других пользователей и удалять их из подписок."""
        test_user = PostsFollowTests.user
        test_author = PostsFollowTests.author
        follow_counter = Follow.objects.count()
        self.assertRedirects(
            self.guest.get(reverse(
                'posts:profile_follow',
                kwargs={'username': test_author.username})
            ),
            '/auth/login/?next=/profile/test_author_1/follow/'
        )
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': test_author.username})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=test_user,
                author=test_author
            ).exists()
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': test_author.username})
        )
        self.assertEqual(Follow.objects.count(), follow_counter)

    def test_user_follow_posts_exist_at_desire_location(self):
        """Новая запись пользователя появляется в ленте тех, кто """
        """на него подписан и не появляется в ленте тех, кто не подписан."""
        test_author = PostsFollowTests.author
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': test_author.username})
        )
        Post.objects.create(
            text='text',
            author=test_author,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        content = response.context['page_obj'][1]
        self.assertEqual(content.text, 'text')

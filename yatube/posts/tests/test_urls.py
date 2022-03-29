from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.urls_access_and_temlates = {
            '/': [False, 'posts/index.html'],
            '/create/': [True, 'posts/create_post.html'],
            f'/group/{cls.group.slug}/': [False, 'posts/group_list.html'],
            f'/profile/{cls.user.username}/': [False, 'posts/profile.html'],
            f'/posts/{cls.post.id}/': [False, 'posts/post_detail.html'],
            f'/posts/{cls.post.id}/edit/': [True, 'posts/create_post.html'],
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_use_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        templates_url_names = {
            url: data[1] for url, data in self.urls_access_and_temlates.items()
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_non_authorized_urls_exist_at_desired_location(self):
        """Проверяем общедоступные страницы и запрос к несуществующей."""
        no_auth_urls = [
            url for url in self.urls_access_and_temlates.keys() if (
                not self.urls_access_and_temlates[url][0]
            )
        ]
        for url in no_auth_urls:
            with self.subTest(address=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_urls_exist_at_desired_location(self):
        """Проверяем страницы для авторизированных пользователей."""
        post_id = self.post.id
        auth_req_urls = {
            f'/posts/{post_id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            f'/posts/{post_id}/comment/': HTTPStatus.FOUND,
        }
        for url, expect_code in auth_req_urls.items():
            with self.subTest(address=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, expect_code)

    def test_redirects_for_non_authorized_users(self):
        """Проверка редиректов для неавторизированных пользователей."""
        post_id = self.post.id
        auth_req_urls = {
            f'/posts/{post_id}/edit/': (
                f'/auth/login/?next=/posts/{post_id}/edit/'
            ),
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{post_id}/comment/': (
                f'/auth/login/?next=/posts/{post_id}/comment/'
            ),
        }
        for url, redirect in auth_req_urls.items():
            response = self.guest_client.get(url, follow=True)
            self.assertRedirects(response, redirect)

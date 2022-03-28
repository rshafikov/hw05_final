from http import HTTPStatus

from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=Group.objects.get(id=1),
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_urls_use_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_non_authorized_urls_exist_at_desired_location(self):
        """Проверяем общедоступные страницы и запрос к несуществующей."""
        no_auth_req_urls = [
            '/',
            '/group/slug/',
            '/profile/HasNoName/',
            '/posts/1/',
            '/unexsisting_page/',
        ]
        for url in no_auth_req_urls:
            if url == '/unexsisting_page/':
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
            else:
                with self.subTest(address=url):
                    response = self.guest_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_urls_exist_at_desired_location(self):
        """Проверяем страницы для авторизированных пользователей."""
        auth_req_urls = {
            '/posts/1/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/posts/1/comment/': HTTPStatus.FOUND,
        }
        for url, expect_code in auth_req_urls.items():
            with self.subTest(address=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, expect_code)

    def test_redirects_for_non_authorized_users(self):
        """Проверка редиректов для неавторизированных пользователей."""
        auth_req_urls = {
            '/posts/1/edit/': '/auth/login/?next=/posts/1/edit/',
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/comment/': '/auth/login/?next=/posts/1/comment/',
        }
        for url, redirect in auth_req_urls.items():
            response = self.guest_client.get(url, follow=True)
            self.assertRedirects(response, redirect)

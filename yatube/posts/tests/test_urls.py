from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostGroupUrlTest(TestCase):
    """Доступность URL-адресов, вызываемые шаблоны."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user_author = User.objects.create_user(
            username='test_user_author'
        )
        cls.user_not_author = User.objects.create_user(
            username='test_user_not_author'
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='тестовый текст',
            group=cls.group,
        )        

    def setUp(self):
        self.authorized_client_post_author = Client()
        self.authorized_client_post_author.force_login(
            self.user_author,
        )
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(
            self.user_not_author,
        )

    def tearDown(self):
        cache.clear()

    def test_urls_exist_at_desired_location_for_all(self):
        """Проверяем общедоступность страниц.

        Для всех пользователей доступны страницы: /posts/1/,
        /profile/test_user/, /group/test_slug/, /, несуществующая
        страница вызывает ошибку 404.
        """
        url_status_code_response = {
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/profile/{self.user_author.username}/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            '': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, status_code in url_status_code_response.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_urls_exist_at_desired_location_for_authorized_post_author(self):
        """Доступность страниц /create/, /posts/1/edit/, /follow_index/.

        Страницы /create/, /follow_index/ доступны авторизированному
        пользователю, страница /posts/1/edit/ доступна ее аторизировнному
        автору.
        """
        url_tupple = (
            f'/posts/{self.post.id}/edit/',
            '/create/',
            '/follow/',
        )
        for url in url_tupple:
            with self.subTest(url=url):
                response = self.authorized_client_post_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_post_edit_url_redirect_ananymos(self):
        """Перенаправления для страниц /posts/1/edit/, /create/.

        Страницы /posts/1/edit/, /create/ перенаправляют неавторизировнного
        пользователя на страницу логина.
        """
        edit_page = f'/posts/{self.post.id}/edit/'
        create_page = '/create/'
        next = '/auth/login/?next='
        url_redirect_address = {
            edit_page: next + edit_page,
            create_page: next + create_page,
        }
        for desired_address, redirect_address in url_redirect_address.items():
            with self.subTest(desired_address=desired_address):
                response = self.client.get(desired_address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_post_edit_redirect_not_author(self):
        """Перенаправление не автора для страницы /posts/1/edit/.

        Страница /posts/1/edit/ перенаправляет авторизированного пользователя,
        не автора поста на страницу /posts/1/.
        """
        response = self.authorized_client_not_author.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_urls_use_correct_templates(self):
        """URL-адрес использует соотетствующий шаблон."""
        url_names_templates = {
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/profile/{self.user_author.username}/': 'posts/profile.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            '/create/': 'posts/create_post.html',
            '': 'posts/index.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client_post_author.get(address)
                self.assertTemplateUsed(response, template)

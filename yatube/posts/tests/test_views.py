import shutil
import tempfile
from unittest import expectedFailure

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..constants import POSTS_PER_PAGE
from ..models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostGroupPagesTest(TestCase):
    """Шаблоны и контекст для имен страниц."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user_author = User.objects.create_user(
            username='test_user',
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='тестовое описание',
        )
        Group.objects.create(
            title='группа без постов',
            slug='no_posts_group',
            description='описание группы без постов',
        )
        Post.objects.create(
            author=cls.user_author,
            text='тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(
            PostGroupPagesTest.user_author
        )

    def tearDown(self):
        cache.clear()

    @expectedFailure
    def test_post_is_created_correct(self, post):
        """Данные передаются верно в созданный пост.

        Самостоятельно не вызывается, только из других методов.
        """
        self.assertEqual(post.text, 'тестовый текст')
        self.assertEqual(post.author.username, 'test_user')
        self.assertEqual(post.group.slug, 'test_slug')

    def test_pages_use_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_names_templates = {
            reverse('posts:post_edit', kwargs={'post_id': 1}):
                'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:profile', kwargs={'username': 'test_user'}):
                'posts/profile.html',
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'}):
                'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for page_name, template in pages_names_templates.items():
            with self.subTest(page_name=page_name):
                response = self.authorized_client_author.get(page_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_posts_profile_pages_show_correct_page_obj(self):
        """Аргумент контекста page_obj.

        Для шаблонов index, group_post, profile в контекст передан
        правильный аргумент page_obj.
        """
        page_names_tupple = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={'username': 'test_user'}),
        )
        for page_name in page_names_tupple:
            with self.subTest(page_name=page_name):
                response = self.authorized_client_author.get(page_name)
                first_object = response.context['page_obj'][0]
                self.test_post_is_created_correct(first_object)

    def test_group_posts_page_show_correct_group_in_context(self):
        """Аргумент контекста group для шаблона group_post."""
        response = (self.authorized_client_author.get(
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'})
        ))
        group = response.context['group']
        self.assertEqual(group.slug, 'test_slug')
        self.assertEqual(group.title, 'тестовая группа')
        self.assertEqual(group.description, 'тестовое описание')

    def test_profile_page_show_correct_author_in_context(self):
        """Аргумент контекста author для шаблона profile."""
        response = (self.authorized_client_author.get(
            reverse('posts:profile', kwargs={'username': 'test_user'})
        ))
        author = response.context['author']
        self.assertEqual(author.username, 'test_user')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        ))
        post = response.context['post']
        self.test_post_is_created_correct(post)

    def test_post_create_post_edit_pages_show_correct_form_in_context(self):
        """Проверка формы в контексте шаблонов post_create и post_edit."""
        page_names_tupple = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        for page_name in page_names_tupple:
            response = self.authorized_client_author.get(page_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_post_and_is_edit_in_context(self):
        """Аргуметы post и is_edit в контексте для шаблона post_edit."""
        response = (self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        ))
        post = response.context['post']
        is_edit = response.context['is_edit']
        self.test_post_is_created_correct(post)
        self.assertTrue(is_edit)

    def test_post_not_in_another_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = (self.authorized_client_author.get(
            reverse('posts:group_posts', kwargs={'slug': 'no_posts_group'})
        ))
        posts = response.context['page_obj']
        self.assertEqual(len(posts), 0)


class PaginatorViewTest(TestCase):
    """Верное колличество выводимых постов на страницу."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.posts_per_second_page = 3
        cls.user_author = User.objects.create_user(
            username='test_user',
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='тестовое описание',
        )
        posts = []
        for _ in range(
            POSTS_PER_PAGE
            + PaginatorViewTest.posts_per_second_page
        ):
            post = Post(
                author=cls.user_author,
                text='тестовый текст',
                group=cls.group,
            )
            posts.append(post)

        Post.objects.bulk_create(posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(
            PaginatorViewTest.user_author
        )

    def test_posts_per_page_for_index_group_post_profile_pages(self):
        """Количество записей на страницах.

        Шаблоны index, group_post, profile создаются с десятью записями
        на первой странице и тремя записями на второй, если общее число
        записей - 13.
        """
        pages_names_tupple = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={'username': 'test_user'}),
        )
        for page_name in pages_names_tupple:
            with self.subTest(page_name=page_name):
                response_first = self.authorized_client.get(page_name)
                response_second = self.authorized_client.get(
                    page_name + '?page=2'
                )
                self.assertEqual(
                    len(response_first.context['page_obj']),
                    POSTS_PER_PAGE
                )
                self.assertEqual(
                    len(response_second.context['page_obj']),
                    PaginatorViewTest.posts_per_second_page
                )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageTest(TestCase):
    """Верное отображение загружаемых картинок."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.user = User.objects.create_user(
            username="test user",
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='тестовое описание',
        )
        Post.objects.create(
            author=cls.user,
            text='тестовый текст',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def tearDown(self):
        cache.clear()

    def test_image_in_context_for_index_group_post_profile(self):
        """Загружаемая пользователем картинка передаётся в контекст.

        Для шаблонов index, group_post, profile аргумент контекста page_obj
        передает загружаемую пользователем картинку.
        """
        pages_tupple = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={'username': 'test user'}),
        )
        for page in pages_tupple:
            with self.subTest(page=page):
                response = self.client.get(page)
                image = response.context['page_obj'][0].image
                self.assertEqual(image, 'posts/small.gif')

    def test_image_in_context_for_post_detail(self):
        """Загружаемая пользователем картинка передаётся в контекст.

        Для шаблона post_detail аргумент контекста post передает загружаемую
        пользователем картинку.
        """
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1}),
        )
        image = response.context['post'].image
        self.assertEqual(image, 'posts/small.gif')


class CommentTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_post_author = User.objects.create_user(
            username='post_author',
        )
        cls.user_comment_author = User.objects.create_user(
            username='comment_author'
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_post_author,
            text='тестовый текст',
            group=cls.group,
        )
        Comment.objects.create(
            author=cls.user_comment_author,
            text='тестовый комментарий',
            post=cls.post
        )

    def test_comment_in_context_for_post_detail(self):
        """Аргумент контекста comment  шаблоне post_detail.

        Шаблон post_detail создается с контекстом, в который верно
        передан комментарий."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        comment = response.context['comments'][0]
        self.assertEqual(comment.author.username, 'comment_author')
        self.assertEqual(comment.text, 'тестовый комментарий')
        self.assertEqual(comment.post.text, 'тестовый текст')


class CacheTest(TestCase):
    """Кеширование."""

    def test_index_page_is_cached(self):
        """Кеширование в шаблоне главной страницы."""
        self.user = User.objects.create_user(
            username="test_user"
        )
        post = Post.objects.create(
            author=self.user,
            text='текст для кеширования',
        )
        response = self.client.get(
            reverse('posts:index')
        )
        post.delete()
        response_after_delete = self.client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            response.content,
            response_after_delete.content
        )
        cache.clear()
        response_after_cache_clear = self.client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(
            response_after_delete.content,
            response_after_cache_clear.content
        )


class FollowTest(TestCase):
    """Корректная работа подписок на авторов."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user_author = User.objects.create_user(
            username='author',
        )
        cls.user_authorized = User.objects.create_user(
            username='test_user',
        )
        cls.user_old_subscriber = User.objects.create_user(
            username='old_subscriber',
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='тестовое описание',
        )
        Post.objects.create(
            author=cls.user_author,
            text='тестовый текст',
            group=cls.group,
        )
        Follow.objects.create(
            user=cls.user_old_subscriber,
            author=cls.user_author
        )

    def setUp(self):
        self.authorized_client_not_subscriber = Client()
        self.authorized_client_old_subscriber = Client()
        self.authorized_client_not_subscriber.force_login(
            FollowTest.user_authorized
        )
        self.authorized_client_old_subscriber.force_login(
            FollowTest.user_old_subscriber
        )

    def test_authorized_user_can_follow(self):
        """Авторизированный пользователь делает подписку.

        При нажатии на кнопку подписаться авторизованным пользователем
        создается новая запись в модели Follow.
        """
        follow_count = Follow.objects.filter(
            user=FollowTest.user_authorized
        ).count()
        self.authorized_client_not_subscriber.get(
            reverse('posts:profile_follow', kwargs={'username': 'author'})
        )
        follow_count_after = Follow.objects.filter(
            user=FollowTest.user_authorized
        ).count()
        self.assertTrue(
            Follow.objects.filter(
                user=FollowTest.user_authorized
            ).filter(
                author=FollowTest.user_author
            ).exists()
        )
        self.assertEqual(
            follow_count + 1,
            follow_count_after
        )

    def test_authorized_user_can_unfollow(self):
        """Авторизованный пользователь может отписаться от автора."""
        follow_count = Follow.objects.filter(
            user=FollowTest.user_old_subscriber
        ).count()
        self.authorized_client_old_subscriber.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'author'})
        )
        follow_count_after = Follow.objects.filter(
            user=FollowTest.user_old_subscriber
        ).count()
        self.assertEqual(
            follow_count - 1,
            follow_count_after
        )
        self.assertFalse(
            Follow.objects.filter(
                user=FollowTest.user_old_subscriber
            ).filter(
                author=FollowTest.user_author
            ).exists()
        )

    def test_post_appear_in_follow_index_for_subscriber(self):
        """Пост автора появляется в ленте подписок его подписчика."""
        response = self.authorized_client_old_subscriber.get(
            reverse('posts:follow_index')
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'тестовый текст')
        self.assertEqual(post.author.username, 'author')
        self.assertEqual(post.group.slug, 'test_slug')

    def test_post_not_appear_in_follow_index_for_not_subscriber(self):
        """Пост не появляется в ленте подписок неподписанного пользователя."""
        response = self.authorized_client_not_subscriber.get(
            reverse('posts:follow_index')
        )
        post_list = response.context['page_obj']
        self.assertEqual(len(post_list), 0)

    def test_profile_page_show_correct_following_in_context(self):
        """Верный аргумент контекста following.

        Страница profile создается с контекстом, в который верно передан
        аргумент following.
        """
        response = self.authorized_client_not_subscriber.get(
            reverse('posts:profile', kwargs={'username': 'author'})
        )
        response_follower = self.authorized_client_old_subscriber.get(
            reverse('posts:profile', kwargs={'username': 'author'})
        )
        self.assertFalse(response.context['following'])
        self.assertTrue(response_follower.context['following'])

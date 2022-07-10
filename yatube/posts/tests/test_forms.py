import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    """Корректная работа формы создания и изменения поста."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='тестовая группа',
            description='тестовое описание',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            text='какой-то текст',
            author=cls.user,
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_authorized_author_create_post_by_form_in_create_page(self):
        """Форма в шаблоне create создает запись в модели Post.

        Валидная форма в шаблоне create от авторизированного пользователя
        создает запись в модели Post.
        """
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'test_user'}
        ))
        self.assertEqual(Post.objects.count(), post_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, 'posts/small.gif')

    def test_authorized_post_author_edit_his_post(self):
        """Валидная форма в шаблоне post_edit изменяет запись в модели Post.

        Авторизированный автор поста может изменить свою запись в модели Post
        через форму на странице post_edit.
        """
        uploaded = SimpleUploadedFile(
            name='new.gif',
            content=self.small_gif,
            content_type='image/gif',
        )
        post_count = Post.objects.count()
        form_data = {
            'text': 'новый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id},
        ))
        self.assertEqual(Post.objects.count(), post_count)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, 'posts/new.gif')

    def test_unauthorized_user_tries_create_post(self):
        """Неавторизированный пользователь не может добавить запись."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'текст не должен появиться',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=/create/'
        )
        self.assertEqual(post_count, Post.objects.count())


class CommentFormTest(TestCase):
    """Корректная работа формы отправки комментария."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_post_author = User.objects.create_user(username='test_user')
        cls.user_not_post_author = User.objects.create_user(
            username='test_user_2'
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            description='тестовое описание',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            text='какой-то текст',
            author=cls.user_post_author,
            group=cls.group,
        )

    def test_authorized_user_adds_comment(self):
        """Автризированный пользователь может оставлять комментарий."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_not_post_author)
        comments_count = self.post.comments.count()
        form_data = {
            'text': 'тестовый комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        comment = Comment.objects.first()
        self.assertEqual(
            self.post.comments.count(),
            comments_count + 1
        )
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user_not_post_author)
        self.assertEqual(comment.post, self.post)

    def test_unauthorized_user_tries_add_comment(self):
        """Неавторизированный пользователь не может оставить комментарий."""
        comments_count = self.post.comments.count()
        form_data = {
            'text': 'текст не должен появиться',
        }
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            comments_count,
            self.post.comments.count()
        )
        self.assertFalse(
            Comment.objects.filter(text=form_data['text']).exists()
        )

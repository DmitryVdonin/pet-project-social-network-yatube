from django.contrib.auth import get_user_model
from django.test import TestCase

from ..constants import CHARS_PER_STR_VIEW
from ..models import Comment, Group, Post

User = get_user_model()


class PostGroupModelTest(TestCase):
    """Корректная работа моделей."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='тестовое описание',
        )
        cls.post = Post.objects.create(
            text='текст' * 100,
            author=cls.user,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_objects_names = {
            self.group: self.group.title,
            self.post: self.post.text[:CHARS_PER_STR_VIEW]
        }
        for object, expected_name in expected_objects_names.items():
            with self.subTest(object=object):
                self.assertEqual(str(object), expected_name)

    def test_group_verbose_names(self):
        """verbose_name в полях модели group совпадает с ожидаемым."""
        group_field_verboses = {
            'title': 'Название',
            'slug': 'Адрес(slug)',
            'description': 'Описание',
        }
        for field, expected_value in group_field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_verbose_names(self):
        """verbose_name в полях модели post совпадает с ожидаемым."""
        post_field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in post_field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_help_text(self):
        """Help_text в полях модели post совпадает с ожидаемым."""
        post_help_text = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in post_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value
                )


class CommentsModelTest(TestCase):
    """Корректная работы комментариев."""

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.group = Group.objects.create(
            title='тестовая группа',
            slug='test_slug',
            description='тестовое описание',
        )
        self.post = Post.objects.create(
            text='текст' * 100,
            author=self.user,
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='тестовый комментарий',
        )

    def test_comment_verbose_names(self):
        """verbose_name в полях модели  совпадает с ожидаемым."""
        comments_field_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Текст',
            'created': 'Дата',
        }
        for field, expected_value in comments_field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_comment_help_text(self):
        """help_text в полях модели  совпадает с ожидаемым."""
        self.assertEqual(
            self.comment._meta.get_field('text').help_text,
            'Ваш комментарий:'
        )

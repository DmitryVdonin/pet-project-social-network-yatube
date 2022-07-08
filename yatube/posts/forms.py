from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма для создания поста(записи)."""

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Форма для комментариев."""

    class Meta:
        model = Comment
        fields = ('text',)

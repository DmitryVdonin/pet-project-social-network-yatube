from django.contrib import admin

from .models import Comment, Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Отображение раздела Post в админ-зоне."""

    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Отображение раздела Group в админ-зоне."""

    list_display = (
        'pk',
        'title',
        'slug',
        'description',
    )
    search_fields = ('title',)
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentsAdmin(admin.ModelAdmin):
    """Отображение комментариев в админ-зоне."""

    list_display = (
        'pk',
        'text',
        'created',
        'author',
        'post',
    )
    search_fields = ('text',)
    list_filter = ('created',)

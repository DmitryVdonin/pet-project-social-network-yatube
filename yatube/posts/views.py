from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .constants import CACHE_TIME_INDEX_PAGE
from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post
from .utils import divider_per_page

User = get_user_model()


@cache_page(CACHE_TIME_INDEX_PAGE, key_prefix="index_page")
def index(request):
    """Отображение главной страницы."""
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group', 'author')
    page_obj = divider_per_page(request, post_list)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):
    """Отображение страниц с группами."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_obj = divider_per_page(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def profile(request, username):
    """Отображение страницы пользователя."""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    page_obj = divider_per_page(request, post_list)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author,
    ).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    """Отображение страницы записи(поста)."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id,
    )
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }

    return render(request, template, context)


@login_required
def post_create(request):
    """Отображение страницы создания новой записи."""
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    result = render(request, template, {'form': form})
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        result = redirect('posts:profile', request.user.username)

    return result


@login_required
def post_edit(request, post_id):
    """Отображение страницы редактирования собственной записи."""
    template = 'posts/create_post.html'
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id,
    )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    result = redirect('posts:post_detail', post_id)
    if post.author == request.user and not form.is_valid():
        result = render(request, template, context)

    if form.is_valid():
        post = form.save()

    return result


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    post = get_object_or_404(
        Post,
        id=post_id,
    )
    form = CommentForm(request.POST or None)
    if form.is_valid:
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница с постами автров, на которых подписан пользователь."""
    template = 'posts/follow.html'
    posts_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = divider_per_page(request, posts_list)
    context = {'page_obj': page_obj}

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author = get_object_or_404(
        User,
        username=username,
    )
    if request.user != author and not Follow.objects.filter(
        user=request.user,
        author=author,
    ).exists():
        Follow.objects.create(
            user=request.user,
            author=author,
        )

    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора."""
    Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)
    ).delete()

    return redirect('posts:index')

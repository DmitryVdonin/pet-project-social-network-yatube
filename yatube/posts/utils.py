from django.core.paginator import Paginator

from .constants import POSTS_PER_PAGE


def divider_per_page(request, post_list):
    """Функция пагинатор."""
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_namber = request.GET.get('page')

    return paginator.get_page(page_namber)

from django.conf import settings
from django.core.paginator import Paginator


def paginator(request, post_list):
    """Return posts on the desired page."""
    post = Paginator(post_list, settings.POSTS_NUM)
    page_number = request.GET.get('page')
    return post.get_page(page_number)

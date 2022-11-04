from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import paginator


def search(request):
    """Search by text and author."""
    if request.method == 'GET':
        query = request.GET.get('q')
        post_list = Post.objects.filter(
            Q(text__icontains=query) | Q(author__username__icontains=query)
        )
        results = all((query, len(post_list) > 0))
        page_obj = paginator(request, post_list)
        context = {
            'query': query,
            'results': results,
            'page_obj': page_obj
        }
        return render(request, 'posts/search_results.html', context)


def index(request):
    """Return the main page."""
    post_list = Post.objects.select_related('author', 'group')
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Return the group page."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_obj = paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Return the profile page"""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('author')
    page_obj = paginator(request, post_list)
    user = request.user
    following = (user.is_authenticated and
                 Follow.objects.filter(user=user, author=author))
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
        'user': user,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Return the post page."""
    post = get_object_or_404(Post, pk=post_id)
    user = request.user
    author = post.author
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post_id=post_id)
    context = {
        'post': post,
        'user': user,
        'author': author,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Return the post creation page."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    context = {
        'form': form
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Return the post edit page."""
    post = get_object_or_404(Post, pk=post_id)
    user = request.user
    if user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_delete(request, post_id):
    """Post author deletes his post."""
    post = get_object_or_404(Post, pk=post_id)
    post.delete()
    return redirect('posts:profile', post.author)


@login_required
def add_comment(request, post_id):
    """Adding a comment."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def comment_delete(request, post_id, comment_id):
    """Comment author deletes his comment."""
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    return redirect('posts:post_detail', comment.post.pk)


@login_required
def follow_index(request):
    """Return the subscription page."""
    user = request.user
    post_list = Post.objects.filter(author__following__user=user)
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Following"""
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Unfollowing"""
    author = get_object_or_404(User, username=username)
    user = request.user
    try:
        follow = Follow.objects.get(
            author=author,
            user=user
        )
    except Follow.DoesNotExist:
        follow = None
    follow.delete()
    return redirect('posts:profile', username=username)

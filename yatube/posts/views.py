from django.shortcuts import render, get_object_or_404, redirect
from core.utils import add_paginator
from .models import Post, Group, Comment
from .forms import PostForm, CommentForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


User = get_user_model()

NUMBER_OF_POSTS = 10


# @cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group', 'author').all()
    page_obj = add_paginator(request, post_list, NUMBER_OF_POSTS)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    # post_list = Post.objects.select_related('group').all()
    post_list = group.posts.all()
    page_obj = add_paginator(request, post_list, NUMBER_OF_POSTS)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    this_user = User.objects.get(username=username)
    post_list = Post.objects.select_related('author').filter(author=this_user)
    page_obj = add_paginator(request, post_list, NUMBER_OF_POSTS)
    context = {
        'this_user': this_user,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = Post.objects.select_related('author').get(pk=post_id)
    comments = Comment.objects.prefetch_related('post').filter(post=post)
    post_author = post.author
    form = CommentForm()
    context = {
        'post': post,
        'post_author': post_author,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:profile", request.user)
        return render(request, template, {'form': form})
    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect("posts:post_detail", post_id)
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect("posts:post_detail", post_id)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm(instance=post)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

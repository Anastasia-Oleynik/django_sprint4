from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Post, Category, Comment
from .forms import ProfileEditForm, PostForm, CommentForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404


User = get_user_model()


def index(request):
    template = 'blog/index.html'

    post_list = (
        Post.objects
        .select_related('author', 'category')
        .filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )
        .annotate(
            comment_count=Count('comments', distinct=True)
        )
        .order_by('-pub_date')
    )

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    post_list = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).select_related(
        'author', 'location', 'category'
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def create_post(request):
    template = 'blog/create.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user

        if not post.pub_date:
            post.pub_date = timezone.now()

        post.save()
        return redirect(
            'blog:profile',
            username=request.user.username
        )

    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, template, context)


@login_required
def edit_post(request, post_id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            request.FILES,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)

    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    user = get_object_or_404(User, username=username)
    posts = user.post_set.select_related('location', 'category').order_by(
        '-pub_date'
    )

    if request.user != user:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now()
        )

    posts = posts.annotate(comment_count=Count('comments'))

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_edit(request, username=None):
    if username is None:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)

    if request.user != user:
        print(request.user)
        print(user)
        raise Http404

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'blog/user.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)

    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'form': form,
            'comments': post.comments.select_related('author').order_by(
                'created_at'
            ),
        }
    )


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
    )

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(
        request,
        'blog/comment.html',
        {
            'form': form,
            'comment': comment,
        }
    )


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment,
        pk=comment_id,
        post_id=post_id,
    )

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request,
        'blog/comment.html',
        {
            'comment': comment,
            'is_delete': True,
        }
    )


def detail_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.pub_date > timezone.now() or not post.is_published:
        if request.user != post.author:
            raise Http404

    comments = post.comments.select_related('author')
    form = CommentForm() if request.user.is_authenticated else None

    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form,
        }
    )


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    form = PostForm(instance=post)

    return render(
        request,
        'blog/create.html',
        {
            'form': form,
            'post': post,
            'is_delete': True,
        }
    )

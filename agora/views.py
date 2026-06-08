import json

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Board, Post


def _clean_uploaded_image(uploaded_file):
    """驗證上傳檔案確實是合法圖片（會用 Pillow 開啟並檢查），擋掉偽裝成圖片的任意檔案。"""
    if not uploaded_file:
        return None
    try:
        forms.ImageField().clean(uploaded_file)
    except ValidationError:
        return None
    return uploaded_file


def agora(request, board_id=None):
    boards = Board.objects.prefetch_related('anis').annotate(
        post_count=Count('posts', distinct=True)
    ).order_by('name')[:50]

    my_boards = Board.objects.none()
    if request.user.is_authenticated:
        my_boards = request.user.following_boards.prefetch_related('anis').annotate(
            post_count=Count('posts', distinct=True)
        ).order_by('name')

    base_qs = Post.objects.filter(parent__isnull=True).select_related(
        'author', 'board'
    ).prefetch_related('board__anis').annotate(reply_count=Count('thread_posts', distinct=True))

    board = None
    mode = 'recent'

    if board_id:
        board = get_object_or_404(
            Board.objects.annotate(
                thread_count=Count('posts', filter=Q(posts__parent__isnull=True), distinct=True)
            ),
            pk=board_id
        )
        posts = base_qs.filter(board=board).order_by('-created_at')
    else:
        feed_boards = Board.objects.none()
        if request.user.is_authenticated:
            feed_boards = Board.objects.filter(
                Q(followers=request.user) | Q(anis__in=request.user.following_anis.all())
            ).distinct()

        if feed_boards.exists():
            posts = base_qs.filter(board__in=feed_boards).order_by('-created_at')
        else:
            mode = 'popular'
            posts = base_qs.order_by('-reply_count', '-created_at')

    posts = posts[:30]

    context = {
        'boards': boards,
        'my_boards': my_boards,
        'board': board,
        'posts': posts,
        'mode': mode,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'agora/partials/post_list.html', context)

    return render(request, 'agora/forum.html', context)


def agora_board_search(request):
    q = request.GET.get('q', '').strip()

    boards = Board.objects.prefetch_related('anis').annotate(
        post_count=Count('posts', distinct=True)
    ).order_by('name')

    if q:
        boards = boards.filter(
            Q(name__icontains=q) |
            Q(anis__title__icontains=q) |
            Q(anis__title_zh__icontains=q) |
            Q(anis__title_ch__icontains=q)
        ).distinct()

    return render(request, 'agora/partials/board_list.html', {'boards': boards})


def agora_thread(request, pk):
    root = get_object_or_404(Post, pk=pk, parent__isnull=True)

    thread_posts = list(
        Post.objects.filter(Q(pk=root.pk) | Q(root=root))
        .select_related('author', 'board')
        .prefetch_related('board__anis')
        .order_by('created_at')
    )

    by_id = {p.id: p for p in thread_posts}
    for p in thread_posts:
        p.children = []
    for p in thread_posts:
        if p.parent_id and p.parent_id in by_id:
            by_id[p.parent_id].children.append(p)

    root_post = by_id[root.id]

    my_boards = Board.objects.none()
    if request.user.is_authenticated:
        my_boards = request.user.following_boards.prefetch_related('anis').annotate(
            post_count=Count('posts', distinct=True)
        ).order_by('name')

    return render(request, 'agora/thread.html', {
        'board': root_post.board,
        'root': root_post,
        'my_boards': my_boards,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def agora_create_post(request, board_id):
    board = get_object_or_404(Board, pk=board_id)
    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()
    image = _clean_uploaded_image(request.FILES.get('image'))

    if title or content or image:
        Post.objects.create(board=board, author=request.user, title=title, content=content, image=image)

    return redirect('agora_board', board_id=board.pk)


@login_required(login_url='/accounts/login/')
@require_POST
def agora_create_reply(request, post_id):
    parent = get_object_or_404(Post, pk=post_id)
    content = request.POST.get('content', '').strip()
    image = _clean_uploaded_image(request.FILES.get('image'))

    if content or image:
        Post.objects.create(board=parent.board, author=request.user, parent=parent, content=content, image=image)

    return redirect('agora_thread', pk=parent.root_id or parent.pk)


@login_required(login_url='/accounts/login/')
@require_POST
def agora_edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, author=request.user)

    if not post.parent_id:
        post.title = request.POST.get('title', '').strip()
    post.content = request.POST.get('content', '').strip()

    image = _clean_uploaded_image(request.FILES.get('image'))
    if image:
        post.image = image
    post.save()

    return redirect('agora_thread', pk=post.root_id or post.pk)


@login_required(login_url='/accounts/login/')
@require_POST
def agora_delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id, author=request.user)

    if post.parent_id:
        redirect_pk = post.root_id or post.parent_id
        post.delete()
        return redirect('agora_thread', pk=redirect_pk)

    board_id = post.board_id
    post.delete()
    return redirect('agora_board', board_id=board_id)


@require_POST
def toggle_follow_board(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
        board_id = data.get('board_id')
        action = data.get('action')

        board = get_object_or_404(Board, pk=board_id)

        if action == 'follow':
            request.user.following_boards.add(board)
        elif action == 'unfollow':
            request.user.following_boards.remove(board)

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

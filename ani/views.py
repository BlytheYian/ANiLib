from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, F, Case, When, Value, IntegerField, Avg
import json
from .models import Ani, Episode, UserReview
from django.utils import timezone
from django.utils.timezone import localtime
from datetime import timedelta, datetime
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


def ani_index(request):
    priority_qs = ['CROWDFUNDING', 'UPCOMING', 'PILOT', 'GREENLIGHT']
    anis_with_priority = Ani.objects.annotate(
        priority_score=Case(
            When(status__in=priority_qs, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by(
        'priority_score',
        F('year').desc(nulls_first=True),
        'title'
    )
    recent_anis = anis_with_priority[:10]
    recommended_anis = anis_with_priority[10:25]

    now = timezone.now()
    one_day = timedelta(days=1)

    window_eps = Episode.objects.filter(
        release_time__gte=(now - one_day)
    ).select_related('ani').order_by('release_time')

    from collections import defaultdict
    ani_eps = defaultdict(list)
    for ep in window_eps:
        ani_eps[ep.ani_id].append(ep)

    best = {}
    for aid, eps in ani_eps.items():
        aired    = [e for e in eps if e.release_time < now]
        upcoming = [e for e in eps if e.release_time >= now]

        if aired:
            latest_aired = aired[-1]
            if upcoming and upcoming[0].release_time <= latest_aired.release_time + one_day:
                best[aid] = upcoming[0]
            else:
                best[aid] = latest_aired
        elif upcoming:
            best[aid] = upcoming[0]

    upcoming_episodes = sorted(best.values(), key=lambda e: e.release_time)[:15]

    cal_eps = Episode.objects.filter(
        release_time__gte=timezone.make_aware(datetime(2026, 1, 1)),
        release_time__lte=(now + timedelta(weeks=6))
    ).select_related('ani').order_by('release_time')

    cal_data = {}
    for ep in cal_eps:
        local_dt = localtime(ep.release_time)
        date_key = local_dt.strftime('%Y-%m-%d')
        if date_key not in cal_data:
            cal_data[date_key] = []
        cal_data[date_key].append({
            'pk': ep.ani.pk,
            'title': ep.ani.title,
            'title_zh': ep.ani.title_zh or '',
            'title_ch': ep.ani.title_ch or '',
            'ep': (f"第{ep.season}季 " if ep.season else "") + f"第{ep.number}集" + (f" - {ep.title}" if ep.title else ""),
            'time': local_dt.strftime('%H:%M'),
            'poster': ep.ani.poster_thumbnail.url if ep.ani.poster else '',
        })

    return render(request, 'ani/ani_index.html', {
        'recent_anis': recent_anis,
        'recommended_anis': recommended_anis,
        'upcoming_episodes': upcoming_episodes,
        'cal_data': cal_data,
    })


def ani_detail(request, pk):
    queryset = Ani.objects.prefetch_related(
        'tags', 'creators', 'studio', 'episodes', 'aliases',
        'characters__va',
    )
    ani = get_object_or_404(queryset, pk=pk)

    user_review = None
    if request.user.is_authenticated:
        user_review = UserReview.objects.filter(user=request.user, ani=ani).first()

    from django.db.models import Count
    rated_qs = ani.reviews.filter(score__isnull=False)
    avg_rating = round(rated_qs.aggregate(avg=Avg('score'))['avg'] or 0, 1) or None
    rating_count = rated_qs.count()
    score_dist = {i: 0 for i in range(1, 11)}
    for row in rated_qs.values('score').annotate(c=Count('score')):
        score_dist[row['score']] = row['c']
    other_reviews_qs = ani.reviews.filter(text__gt='').select_related('user').order_by('-updated_at')
    if request.user.is_authenticated:
        other_reviews_qs = other_reviews_qs.exclude(user=request.user)
    other_reviews = other_reviews_qs[:30]

    ani_creators = list(ani.creators.all())
    characters   = list(ani.characters.select_related('va').order_by('order', 'name'))
    char_data    = [
        {
            'id':          c.id,
            'image':       c.image.url if c.image else None,
            'name':        c.name,
            'name_zh':     c.name_zh or '',
            'va':          c.va.name if c.va else '',
            'description': c.description or '',
            'focus_x':     c.image_focus_x,
            'focus_y':     c.image_focus_y,
            'scale':       c.image_scale,
        }
        for c in characters
    ]

    return render(request, 'ani/ani_detail.html', {
        'ani': ani,
        'ani_creators': ani_creators,
        'characters': characters,
        'char_data': char_data,
        'user_review': user_review,
        'avg_rating': avg_rating,
        'rating_count': rating_count,
        'other_reviews': other_reviews,
        'score_dist': score_dist,
    })


def ani_lib(request):
    sort_by       = request.GET.get('sort', '-year')
    status_filter = request.GET.get('status')
    indie_only    = request.GET.get('indie') == '1'

    anis = Ani.objects.all()

    if status_filter:
        anis = anis.filter(status=status_filter)
    if indie_only:
        anis = anis.filter(tags__tag_name__iexact='Indie')

    if sort_by == 'rating':
        anis = anis.order_by('-imdb_stars', 'title')
    else:
        anis = anis.order_by(F('year').desc(nulls_first=True), 'title')

    anis = anis.distinct()

    paginator = Paginator(anis, 40)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'ani/partials/ani_items.html', {'page_obj': page_obj})

    return render(request, 'ani/ani_lib.html', {
        'page_obj':   page_obj,
        'indie_only': indie_only,
        'statuses':   Ani.StatusChoices.choices,
    })


def ani_search(request):
    query = request.GET.get('q', '').strip()

    results = Ani.objects.none()

    if query:
        import zhconv
        query_tw = zhconv.convert(query, 'zh-tw')
        query_cn = zhconv.convert(query, 'zh-cn')
        queries = list(dict.fromkeys([query, query_tw, query_cn]))
        def _q_any(field):
            return Q(**{f'{field}__icontains': queries[0]}) if len(queries) == 1 else \
                   Q(**{f'{field}__icontains': queries[0]}) | \
                   Q(**{f'{field}__icontains': queries[1]}) | \
                   (Q(**{f'{field}__icontains': queries[2]}) if len(queries) > 2 else Q())

        results = Ani.objects.filter(
            _q_any('title') | _q_any('title_zh') | _q_any('title_ch') |
            _q_any('creators__name') | _q_any('aliases__title') |
            _q_any('characters__name') | _q_any('characters__name_zh') |
            _q_any('characters__va__name')
        ).annotate(
            relevance_score=Case(
                *[When(**{f'{f}__iexact': q}, then=Value(100))
                  for f in ('title', 'title_zh', 'title_ch', 'aliases__title')
                  for q in queries],
                *[When(**{f'{f}__istartswith': q}, then=Value(80))
                  for f in ('title', 'title_zh', 'title_ch', 'aliases__title')
                  for q in queries],
                *[When(**{f'{f}__icontains': q}, then=Value(60))
                  for f in ('title', 'title_zh', 'title_ch', 'aliases__title')
                  for q in queries],
                default=Value(40),
                output_field=IntegerField(),
            )
        ).distinct().order_by('-relevance_score', '-year', 'title')

    if not query and not request.headers.get('HX-Request'):
        return redirect('ani_lib')

    paginator = Paginator(results, 40)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'ani/partials/ani_items.html', {'page_obj': page_obj})

    return render(request, 'ani/ani_search.html', {
        'query': query,
        'page_obj': page_obj,
        'count': results.count(),
    })


@require_POST
@login_required
def submit_review(request, pk):
    ani = get_object_or_404(Ani, pk=pk)
    try:
        data = json.loads(request.body)
        score = data.get('score')
        text = data.get('text', '').strip()

        if score is not None:
            score = int(score)
            if not 1 <= score <= 10:
                return JsonResponse({'error': 'invalid score'}, status=400)

        if len(text) > 200:
            return JsonResponse({'error': '評論超過 200 字'}, status=400)

        review, _ = UserReview.objects.get_or_create(user=request.user, ani=ani)
        if score is not None:
            review.score = score
        review.text = text
        review.save()

        rated_qs = ani.reviews.filter(score__isnull=False)
        avg = rated_qs.aggregate(avg=Avg('score'))['avg']
        return JsonResponse({
            'status': 'ok',
            'score': review.score,
            'avg': round(avg, 1) if avg else None,
            'count': rated_qs.count(),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_POST
def toggle_follow_animation(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
        animation_id = data.get('animation_id')
        action = data.get('action')

        ani = get_object_or_404(Ani, pk=animation_id)

        if action == 'follow':
            request.user.following_anis.add(ani)
        elif action == 'unfollow':
            request.user.following_anis.remove(ani)

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)



from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q,F,Case, When, Value, IntegerField
from .models import Ani, Episode
from django.utils import timezone
from datetime import timedelta

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
    future_episodes = Episode.objects.filter(release_time__gte=(now - timedelta(days=1))).select_related('ani').order_by('release_time')
    upcoming_episodes = []
    seen_ani_ids = set()
    for ep in future_episodes:
        if ep.ani_id not in seen_ani_ids:
            upcoming_episodes.append(ep)
            seen_ani_ids.add(ep.ani_id)
            if len(upcoming_episodes) == 15:
                break

    return render(request, 'ani/ani_index.html', {
        'recent_anis': recent_anis,
        'recommended_anis': recommended_anis,
        'upcoming_episodes': upcoming_episodes,
    })

def ani_detail(request, pk):
    queryset = Ani.objects.prefetch_related('tags', 'creators', 'studio')
    ani = get_object_or_404(queryset, pk=pk)
    return render(request, 'ani/ani_detail.html', {'ani': ani})

'''def ani_lib(request):
    all_anis = Ani.objects.all().order_by('-year')
    return render(request, 'ani/ani_lib.html', {'anis': all_anis})'''
    
def ani_lib(request):
    sort_by = request.GET.get('sort', '-year')
    status_filter = request.GET.get('status')
    
    anis = Ani.objects.all()
    
    if status_filter:
        anis = anis.filter(status=status_filter)

    if sort_by == 'rating':
        anis = anis.order_by('-imdb_stars', 'title')
    else:
        anis = anis.order_by(F('year').desc(nulls_first=True), 'title')

    paginator = Paginator(anis, 40)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'ani/partials/ani_items.html', {'page_obj': page_obj})

    return render(request, 'ani/ani_lib.html', {'page_obj': page_obj})

def ani_search(request):
    query = request.GET.get('q', '').strip()
    
    results = Ani.objects.none() 
    
    if query:
        results = Ani.objects.filter(
            Q(title__icontains=query) |
            Q(title_zh__icontains=query) | 
            Q(title_ch__icontains=query) |
            Q(creators__name__icontains=query)
        ).annotate(
            relevance_score=Case(
                When(title__iexact=query, then=Value(100)),
                When(title_zh__iexact=query, then=Value(100)),
                When(title_ch__iexact=query, then=Value(100)),
                
                When(title__istartswith=query, then=Value(80)),
                When(title_zh__istartswith=query, then=Value(80)),
                When(title_ch__istartswith=query, then=Value(80)),
                
                When(title__icontains=query, then=Value(60)),
                When(title_zh__icontains=query, then=Value(60)),
                When(title_ch__icontains=query, then=Value(60)),
                
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
        'count': results.count() 
    })
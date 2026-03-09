from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q,Case, When, Value, IntegerField
from .models import Ani

def ani_index(request):
    priority_qs = Ani.objects.filter(
        status__in=['CROWDFUNDING', 'UPCOMING']
    ).order_by('-year','title')[:10]
    
    priority_ids = list(priority_qs.values_list('id', flat=True))
    
    num_needed = 10 - len(priority_ids)
    
    filler_qs = Ani.objects.exclude(id__in=priority_ids).order_by('-year','title')[:num_needed]
    filler_ids = list(filler_qs.values_list('id', flat=True))
    
    recent_anis = list(priority_qs) + list(filler_qs)
    
    all_used_ids = priority_ids + filler_ids
    recommended_anis = Ani.objects.exclude(id__in=all_used_ids).order_by('-year','title')[:15]
    
    return render(request, 'ani/ani_index.html', {
        'recent_anis': recent_anis,
        'recommended_anis': recommended_anis,
    })

def ani_detail(request, pk):
    ani = get_object_or_404(Ani, pk=pk)
    return render(request, 'ani/ani_detail.html', {'ani': ani})

'''def ani_lib(request):
    all_anis = Ani.objects.all().order_by('-year')
    return render(request, 'ani/ani_lib.html', {'anis': all_anis})'''

from django.core.paginator import Paginator

from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
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
    
def ani_lib(request):
    sort_by = request.GET.get('sort', '-year')
    if sort_by == 'rating':
        anis = Ani.objects.all().order_by('-imdb_stars', 'title')
    else:
        anis = Ani.objects.all().order_by('-year', 'title')

    paginator = Paginator(anis, 40)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'ani/partials/ani_items.html', {'page_obj': page_obj})

    return render(request, 'ani/ani_lib.html', {'page_obj': page_obj})
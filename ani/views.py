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
# 記得引入你的 Ani 模型

def ani_search(request):
    query = request.GET.get('q', '').strip()
    
    results = Ani.objects.none() 
    
    if query:
        results = Ani.objects.filter(
            Q(title__icontains=query) |
            Q(title_zh__icontains=query) | 
            Q(title_ch__icontains=query) |
            Q(creators__name__icontains=query) # 假設你的外鍵欄位是 creators__name
        ).annotate(
            # 👇 這裡開始幫每部動畫打分數！
            relevance_score=Case(
                # 1. 完全一模一樣 (iexact 代表不分大小寫的完全相等)
                When(title__iexact=query, then=Value(100)),
                When(title_zh__iexact=query, then=Value(100)),
                When(title_ch__iexact=query, then=Value(100)),
                
                # 2. 以關鍵字開頭 (istartswith)
                When(title__istartswith=query, then=Value(80)),
                When(title_zh__istartswith=query, then=Value(80)),
                When(title_ch__istartswith=query, then=Value(80)),
                
                # 3. 標題包含關鍵字
                When(title__icontains=query, then=Value(60)),
                When(title_zh__icontains=query, then=Value(60)),
                When(title_ch__icontains=query, then=Value(60)),
                
                # 4. 其他狀況 (例如是創作者名字搜到的) 就給基本分 40
                default=Value(40),
                output_field=IntegerField(),
            )
        ).distinct().order_by('-relevance_score', '-year', 'title')
        
    if not query and not request.headers.get('HX-Request'):
        return redirect('ani_lib')
        
    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'ani/partials/ani_items.html', {'page_obj': page_obj})

    return render(request, 'ani/ani_search.html', {
        'query': query,
        'page_obj': page_obj,
        # 因為前面把預設值改成了 Ani.objects.none()，這裡可以直接安全地呼叫 .count()
        'count': results.count() 
    })
    
def ani_lib(request):
    sort_by = request.GET.get('sort', '-year')
    if sort_by == 'rating':
        anis = Ani.objects.all().order_by('-imdb_stars', 'title')
    else:
        anis = Ani.objects.all().order_by('-year', 'title')

    paginator = Paginator(anis, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'ani/partials/ani_items.html', {'page_obj': page_obj})

    return render(request, 'ani/ani_lib.html', {'page_obj': page_obj})
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Ani

def ani_index(request):
    priority_qs = Ani.objects.filter(
        status__in=['CROWDFUNDING', 'UPCOMING']
    ).order_by('-year')[:10]
    
    priority_ids = list(priority_qs.values_list('id', flat=True))
    
    num_needed = 10 - len(priority_ids)
    
    filler_qs = Ani.objects.exclude(id__in=priority_ids).order_by('-year')[:num_needed]
    filler_ids = list(filler_qs.values_list('id', flat=True))
    
    recent_anis = list(priority_qs) + list(filler_qs)
    
    all_used_ids = priority_ids + filler_ids
    recommended_anis = Ani.objects.exclude(id__in=all_used_ids).order_by('-year')[:15]
    
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

def ani_search(request):
    query = request.GET.get('q', '').strip() # 取得網址列的 ?q=關鍵字
    results = []
    
    if query:
        # 同時搜尋 標題(title) 和 描述(description)
        # icontains 代表不分大小寫的模糊比對
        results = Ani.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        ).distinct() # 避免重複抓取
        
    if not query:
    # 如果使用者只打了空格就按搜尋，直接回傳空結果或重新整理
        return redirect('ani_lib')
        
    return render(request, 'ani/ani_search.html', {
        'query': query,
        'results': results,
        'count': results.count() if query else 0
    })
    
def ani_lib(request):
    sort_by = request.GET.get('sort', '-year')
    if sort_by == 'rating':
        anis = Ani.objects.all().order_by('-imdb_stars')
    else:
        anis = Ani.objects.all().order_by('-year')

    paginator = Paginator(anis, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('HX-Request'):
        return render(request, 'ani/partials/ani_items.html', {'page_obj': page_obj})

    return render(request, 'ani/ani_lib.html', {'page_obj': page_obj})
from django.shortcuts import render, get_object_or_404
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
    recommended_anis = Ani.objects.exclude(id__in=all_used_ids).order_by('-year')[:10]
    
    return render(request, 'ani/ani_index.html', {
        'recent_anis': recent_anis,
        'recommended_anis': recommended_anis,
    })

def ani_detail(request, pk):
    ani = get_object_or_404(Ani, pk=pk)
    return render(request, 'ani/ani_detail.html', {'ani': ani})

def ani_lib(request):
    all_anis = Ani.objects.all().order_by('-year')
    return render(request, 'ani/ani_lib.html', {'anis': all_anis})
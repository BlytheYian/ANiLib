from django.shortcuts import render, get_object_or_404
from .models import Ani

def ani_index(request):
    recent_anis = Ani.objects.all().order_by('-year')[:10]
    all_anis = Ani.objects.all().order_by('-year')
    return render(request, 'ani/ani_index.html', {
        'recent_anis': recent_anis,
        'anis': all_anis,
    })

def ani_detail(request, pk):
    ani = get_object_or_404(Ani, pk=pk)
    return render(request, 'ani/ani_detail.html', {'ani': ani})

def ani_lib(request):
    all_anis = Ani.objects.all().order_by('-year')
    return render(request, 'ani/ani_lib.html', {'anis': all_anis})
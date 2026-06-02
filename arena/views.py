from django.shortcuts import render

def arena(request):
    return render(request, 'arena/arena.html')
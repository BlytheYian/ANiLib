from django.shortcuts import redirect,render
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F
from .forms import CustomUserCreationForm

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(request.GET.get('next', '/'))
        else:
            print("錯誤原因：", form.errors) 
            
            error_msg = "註冊失敗，請檢查資料格式。"
            if form.errors:
                error_msg = list(form.errors.values())[0][0] 
                
            return JsonResponse({"error": error_msg}, status=400)
            
    return redirect('/')

@login_required(login_url='/accounts/login/')
def accounts_liked(request):
    anis = request.user.following_anis.all().order_by('-year', 'title')
    anis = anis.order_by(F('year').desc(nulls_first=True), 'title')
    
    paginator = Paginator(anis, 40)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    if request.headers.get('HX-Request'):
        return render(request, 'ani/partials/ani_items.html', {'page_obj': page_obj})
        
    return render(request, 'accounts/accounts_liked.html', {'page_obj': page_obj})

@login_required(login_url='/accounts/login/')
def accounts(request):
    available_avatars = [
        {'file': 'avatar_default.png', 'name': '預設頭像 1'},
    ]

    if request.method == 'POST':
        request.user.username = request.POST.get('username', request.user.username)
        request.user.email = request.POST.get('email', request.user.email)
        
        avatar_selection = request.POST.get('avatar')
        # 提取出所有合法的檔名（file）進行驗證
        valid_avatar_files = [avatar['file'] for avatar in available_avatars]
        if avatar_selection in valid_avatar_files:
            request.user.avatar = avatar_selection
            
        request.user.save()
        return redirect('accounts')

    return render(request, 'accounts/accounts.html', {'available_avatars': available_avatars})
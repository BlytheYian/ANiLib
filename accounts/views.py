from django.shortcuts import redirect,render
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth import get_user_model

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
        {'file': 'avatar_default.png', 'name': '佔位符'},
    ]

    if request.method == 'POST':
        new_username = request.POST.get('username', '').strip()
        new_email = request.POST.get('email', '').strip()
        avatar_selection = request.POST.get('avatar')
        
        has_changed = False

        if new_username and new_username != request.user.username:
            User = get_user_model()
            if User.objects.filter(username=new_username).exists():
                messages.error(request, '此使用者名稱已有人使用，請換一個！')
                return redirect('accounts')
            request.user.username = new_username
            has_changed = True
            
        if new_email and new_email != request.user.email:
            request.user.email = new_email
            has_changed = True
        
        valid_avatar_files = [avatar['file'] for avatar in available_avatars]
        if avatar_selection and avatar_selection in valid_avatar_files and avatar_selection != request.user.avatar:
            request.user.avatar = avatar_selection
            has_changed = True
            
        if has_changed:
            request.user.save()
            messages.success(request, '個人資料已成功更新！')
        else:
            messages.info(request, '資料未進行任何修改。')
            
        return redirect('accounts')

    return render(request, 'accounts/accounts.html', {'available_avatars': available_avatars})
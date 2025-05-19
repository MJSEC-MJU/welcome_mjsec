from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET
from django.http import JsonResponse
def login_view(request):
    if request.user.is_authenticated:
        return redirect("challenges:feeds")
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('challenges:feeds')
        else:
            messages.error(request, "아이디 또는 패스워드가 올바르지 않습니다.")
    
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "성공적으로 로그아웃되었습니다.")
    return redirect('accounts:login')
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("challenges:feeds")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "회원가입이 완료되었습니다. 로그인해주세요.")
            return redirect("accounts:login")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})
@require_GET
def validate_username(request):
    username = request.GET.get('username', '').strip()
    is_taken = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'is_taken': is_taken})
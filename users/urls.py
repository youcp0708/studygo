"""
users/urls.py
前端頁面路由（返回 HTML 模板）
掛載於 studygo/urls.py → path('', include('users.urls'))
"""

from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.conf import settings


def _login_context(extra=None):
    ctx = {'google_client_id': settings.GOOGLE_CLIENT_ID}
    if extra:
        ctx.update(extra)
    return ctx


def index_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/login.html', _login_context())


def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/login.html', _login_context())


def register_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/login.html', _login_context({'show_register': True}))


def logout_page(request):
    """
    登出：清除 Django session + Auth Token，並重定向到登入頁面。
    """
    # 刪除 Auth Token（若存在）
    if request.user.is_authenticated:
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
    # 登出 Django session
    auth_logout(request)
    return render(request, 'users/logout_redirect.html')


def profile_setup_page(request):
    """填寫個人資料頁（Step 2）"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    if hasattr(request.user, 'student_profile'):
        return redirect('dashboard')
    return render(request, 'users/profile_setup.html', {'user': request.user})


def dashboard_page(request):
    """儀表板首頁 — 需要 session 登入"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    context = {'user': request.user}
    if hasattr(request.user, 'student_profile'):
        context['profile'] = request.user.student_profile
    return render(request, 'users/dashboard.html', context)


def edit_profile_page(request):
    """編輯個人資料頁 — 需要 session 登入"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    context = {'user': request.user}
    if hasattr(request.user, 'student_profile'):
        context['profile'] = request.user.student_profile
    return render(request, 'users/edit_profile.html', context)


def forgot_password_page(request):
    return render(request, 'users/forgot_password.html')


def reset_password_page(request):
    """密碼重設頁（由 Email 連結導入）"""
    uid   = request.GET.get('uid', '')
    token = request.GET.get('token', '')
    return render(request, 'users/reset_password.html', {'uid': uid, 'token': token})


urlpatterns = [
    path('',                index_view,           name='index'),
    path('login/',          login_page,           name='login_page'),
    path('register/',       register_page,        name='register_page'),
    path('logout/',         logout_page,          name='logout_page'),
    path('profile/setup/',  profile_setup_page,   name='profile_setup'),
    path('dashboard/',      dashboard_page,       name='dashboard'),
    path('profile/edit/',   edit_profile_page,    name='edit_profile'),
    path('forgot-password/', forgot_password_page, name='forgot_password'),
    path('reset-password/', reset_password_page,  name='reset_password'),
]

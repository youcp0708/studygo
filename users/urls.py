"""
users/urls.py
前端頁面路由（返回 HTML 模板）
掛載於 readyto/urls.py → path('', include('users.urls'))
"""

from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.utils.translation import gettext as _


def _login_context(extra=None):
    ctx = {'google_client_id': settings.GOOGLE_CLIENT_ID}
    if extra:
        ctx.update(extra)
    return ctx


def _email_verification_required():
    """是否強制 Email 驗證（demo 環境可在 .env 關閉）"""
    return getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False)


def _authenticated_redirect(request):
    """已登入使用者的跳轉邏輯（抽出共用）"""
    user = request.user
    if _email_verification_required() and not user.email_verified:
        # 未驗證信箱：顯示登入頁（JS 端會依 localStorage 決定是否顯示驗證等待面板）
        return render(request, 'users/login.html', _login_context())
    if not hasattr(user, 'student_profile') or user.student_profile is None:
        return redirect('profile_setup')
    return redirect('dashboard')


def index_view(request):
    from .models import AlumniShare
    # 首頁學長姐區塊：顯示最新的真實分享（與分享區同一卡片元件）
    recent_shares = AlumniShare.objects.filter(is_active=True).select_related('user')[:6]

    user = request.user
    if user.is_authenticated:
        return _authenticated_redirect(request)
    return render(request, 'users/home.html', {'recent_shares': recent_shares})


def faq_page(request):
    """常見問題頁（獨立頁面，不需登入即可查看）"""
    user = request.user
    profile = getattr(user, 'student_profile', None) if user.is_authenticated else None
    return render(request, 'users/faq.html', {'user': user, 'profile': profile})


def login_page(request):
    if request.user.is_authenticated:
        return _authenticated_redirect(request)
    return render(request, 'users/login.html', _login_context())


def register_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/login.html', _login_context({'show_register': True}))


def logout_page(request):
    """
    登出：清除 Django session，並重定向到登入頁面。
    """
    auth_logout(request)
    return render(request, 'users/logout_redirect.html')


def profile_setup_page(request):
    """填寫個人資料頁（Step 2）"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    if _email_verification_required() and not request.user.email_verified:
        return redirect('/login/?need_verify=1')
    if hasattr(request.user, 'student_profile'):
        return redirect('dashboard')

    # 系所清單改由資料庫提供（Django Admin 可管理），依學院分組
    from django.utils import translation
    from .models import Department
    lang = (translation.get_language() or 'zh-hant').lower()
    faculties = []
    _faculty_index = {}
    for dept in Department.objects.filter(is_active=True):
        faculty_label = dept.get_localized_faculty(lang) or ''
        if faculty_label not in _faculty_index:
            _faculty_index[faculty_label] = {'label': faculty_label, 'departments': []}
            faculties.append(_faculty_index[faculty_label])
        _faculty_index[faculty_label]['departments'].append({
            'value': dept.name,  # 存中文名稱，與既有資料格式一致
            'label': dept.get_localized_name(lang),
        })

    return render(request, 'users/profile_setup.html', {
        'user': request.user,
        'faculties': faculties,
    })


def dashboard_page(request):
    """儀表板首頁 — 需要 session 登入"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    if _email_verification_required() and not request.user.email_verified:
        return redirect('login_page')
    if not hasattr(request.user, 'student_profile') or request.user.student_profile is None:
        return redirect('profile_setup')
    profile = request.user.student_profile

    # 首次導覽（Dashboard Product Tour）設定：在後端組好 dict，
    # 前端透過 json_script 讀取，避免把未加引號的 Django 變數直接塞進 <script> 裡的 JS
    tour_config = {
        'hasSeenTour': profile.has_seen_dashboard_tour,
        'markSeenUrl': reverse('api_dashboard_tour_seen'),
        'nextText': _('下一個'),
        'skipText': _('跳過'),
        'finishText': _('開始使用'),
        'steps': [
            {'targets': ['tourNavHome', 'tourNavTasks', 'tourNavGuide', 'tourNavAlumni', 'tourNavFaq'],
             'title': _('導覽列'),
             'desc': _('首頁、任務清單、資訊中心、學長姐分享、常見問題，都可以從這裡快速前往。')},
            {'targets': ['searchWrap', 'langWrap', 'tourNavReminder', 'tourNavUser'], 'title': _('語言與帳號'),
             'desc': _('這裡可以搜索内容、切換網站語言、查看通知，或前往編輯個人資料。')},
            {'targets': ['dashCardCompletion'], 'title': _('任務完成率'),
             'desc': _('這裡顯示你目前完成了多少準備事項，隨時回來查看整體進度。')},
            {'targets': ['dashCardReminder'], 'title': _('即將到期 / 提醒'),
             'desc': _('重要期限與通知都會顯示在這裡，別錯過任何截止日。')},
            {'targets': ['dashCardAdmission'], 'title': _('目前入學狀態'),
             'desc': _('這裡顯示你目前的入學狀態與就讀學校。')},
            {'targets': ['dashProfileCard'], 'title': _('個人資料卡'),
             'desc': _('你的基本資料都在這裡，可以隨時點擊編輯。')},
            {'targets': ['dashTasksPanel'], 'title': _('近期待辦任務'),
             'desc': _('這裡列出你接下來需要完成的任務，點擊可以查看詳細內容。')},
            {'targets': ['chatFab'], 'title': _('AI 小幫手'),
             'desc': _('有任何問題都可以點這裡問 AI 小幫手，24 小時隨時待命。')},
        ],
    }

    context = {'user': request.user, 'profile': profile, 'tour_config': tour_config}
    return render(request, 'users/dashboard.html', context)


def edit_profile_page(request):
    """編輯個人資料頁 — 需要 session 登入，且需已完成 profile setup"""
    if not request.user.is_authenticated:
        return redirect('login_page')
    if not hasattr(request.user, 'student_profile'):
        return redirect('profile_setup')
    context = {'user': request.user, 'profile': request.user.student_profile}
    return render(request, 'users/edit_profile.html', context)


def alumni_page(request):
    """
    學長姐分享區（左側分頁導覽）：
    - 我的分享：發佈表單（標題＋內容，自動以「學校＋系所」身份發佈）＋ 自己發過的分享
    - 我的學校：只看與使用者同校的分享；可依系所篩選（預設為使用者自己的系所）＋ 文字搜尋
    - 所有學校：全部分享；可依學校、系所篩選 ＋ 文字搜尋
    """
    from django.db.models import Q
    from .models import AlumniShare, StudentProfile, Department

    if not request.user.is_authenticated:
        return redirect('login_page')
    if not hasattr(request.user, 'student_profile'):
        return redirect('profile_setup')

    profile = request.user.student_profile

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()[:200]
        content = (request.POST.get('content') or '').strip()

        if content:
            AlumniShare.objects.create(
                user=request.user,
                university=profile.university,
                nationality=profile.nationality,
                program=(profile.department or '').strip(),  # 系所自動快照，不由表單填寫
                title=title,
                content=content[:1000],
            )
        # PRG：避免重新整理重複發佈
        return redirect('/alumni/?tab=mine')

    tab = request.GET.get('tab') or 'mine'
    if tab not in ('mine', 'school', 'all'):
        tab = 'mine'

    q = (request.GET.get('q') or '').strip()
    # 系所預設「所有系所」（不預先帶入使用者自己的系所）
    selected_dept = (request.GET.get('dept') or '').strip()
    # 「所有學校」分頁：第一次進來（網址沒有 school 參數）預設用使用者自己的學校
    if 'school' in request.GET:
        selected_school = (request.GET.get('school') or '').strip()
    else:
        selected_school = profile.university if tab == 'all' else ''

    base_qs = AlumniShare.objects.filter(is_active=True).select_related('user')

    if tab == 'mine':
        shares = base_qs.filter(user=request.user)
        dept_scope = base_qs.none()
    elif tab == 'school':
        dept_scope = base_qs.filter(university=profile.university)
        shares = dept_scope
    else:  # all
        dept_scope = base_qs
        if selected_school:
            dept_scope = dept_scope.filter(university=selected_school)
        shares = dept_scope

    # 系所下拉選項：依目前選定的學校，列出該校完整系所清單（不限於已有人發文的系所）
    relevant_school = profile.university if tab == 'school' else selected_school
    if relevant_school:
        dept_options = list(
            Department.objects.filter(university=relevant_school, is_active=True)
            .values_list('name', flat=True)
        )
        # 使用者自己的系所永遠在選項中（即使系所清單裡沒收錄）
        own = (profile.department or '').strip()
        if tab == 'school' and own and own not in dept_options:
            dept_options.append(own)
    else:
        # 所有學校且未指定特定學校：退回目前範圍內實際出現過的系所
        dept_options = sorted(set(
            dept_scope.exclude(program='').values_list('program', flat=True)
        ))

    if tab in ('school', 'all'):
        if selected_dept:
            shares = shares.filter(program=selected_dept)
        if q:
            shares = shares.filter(
                Q(title__icontains=q) | Q(content__icontains=q) | Q(program__icontains=q)
            )

    return render(request, 'users/alumni.html', {
        'user': request.user,
        'profile': profile,
        'tab': tab,
        'shares': shares,
        'q': q,
        'selected_dept': selected_dept,
        'selected_school': selected_school,
        'dept_options': dept_options,
        'school_options': StudentProfile.UNIVERSITY_CHOICES,
    })


def alumni_delete(request):
    """刪除自己發佈的分享（僅限本人）。"""
    from .models import AlumniShare
    if not request.user.is_authenticated:
        return redirect('login_page')
    if request.method == 'POST':
        share_id = request.POST.get('share_id')
        AlumniShare.objects.filter(id=share_id, user=request.user).delete()
    return redirect('/alumni/?tab=mine')


def alumni_edit(request):
    """編輯自己發佈的分享（僅限本人）。"""
    from .models import AlumniShare
    if not request.user.is_authenticated:
        return redirect('login_page')
    if request.method == 'POST':
        share_id = request.POST.get('share_id')
        title = (request.POST.get('title') or '').strip()[:200]
        content = (request.POST.get('content') or '').strip()[:1000]
        if content:
            AlumniShare.objects.filter(id=share_id, user=request.user).update(title=title, content=content)
    return redirect('/alumni/?tab=mine')


def privacy_policy_page(request):
    return render(request, 'users/privacy_policy.html')


def terms_of_service_page(request):
    return render(request, 'users/terms_of_service.html')


def forgot_password_page(request):
    return render(request, 'users/forgot_password.html')


def reset_password_page(request):
    """密碼重設頁（由 Email 連結導入）"""
    uid   = request.GET.get('uid', '')
    token = request.GET.get('token', '')
    return render(request, 'users/reset_password.html', {'uid': uid, 'token': token})


urlpatterns = [
    path('',                index_view,           name='index'),
    path('faq/',            faq_page,             name='faq_page'),
    path('login/',          login_page,           name='login_page'),
    path('register/',       register_page,        name='register_page'),
    path('logout/',         logout_page,          name='logout_page'),
    path('profile/setup/',  profile_setup_page,   name='profile_setup'),
    path('dashboard/',      dashboard_page,       name='dashboard'),
    path('profile/edit/',   edit_profile_page,    name='edit_profile'),
    path('alumni/',         alumni_page,          name='alumni'),
    path('alumni/delete/',  alumni_delete,        name='alumni_delete'),
    path('alumni/edit/',    alumni_edit,          name='alumni_edit'),
    path('forgot-password/', forgot_password_page, name='forgot_password'),
    path('reset-password/', reset_password_page,  name='reset_password'),
    path('privacy-policy/', privacy_policy_page,  name='privacy_policy'),
    path('terms-of-service/', terms_of_service_page, name='terms_of_service'),
]

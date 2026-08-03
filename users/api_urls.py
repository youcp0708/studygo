"""
users/api_urls.py
API 路由 — 對應前端 JS 中所有 fetch() 呼叫的 URL
掛載於 readyto/urls.py → path('api/', include('users.api_urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── 帳號認證 ──────────────────────────────────────
    # POST  /api/users/register/           → 註冊新帳號
    path('users/register/',          views.register_view,           name='api_register'),

    # POST  /api/users/login/              → 登入，回傳 Token
    path('users/login/',             views.login_view,              name='api_login'),

    # POST  /api/users/logout/             → 登出（需 Token）
    path('users/logout/',            views.logout_view,             name='api_logout'),

    # ── 使用者資料 ──────────────────────────────────────
    # GET   /api/users/me/                 → 取得當前使用者完整資料（含 Profile）
    path('users/me/',                views.me_view,                 name='api_me'),

    # ── 學生資料 ───────────────────────────────────────
    # GET   /api/users/profile/            → 取得 StudentProfile
    # POST  /api/users/profile/            → 初次建立 StudentProfile（Step 2 填寫資料）
    path('users/profile/',           views.profile_setup_view,      name='api_profile'),

    # PATCH /api/users/profile/update/     → 更新基本資料（編輯頁面用）
    path('users/profile/update/',    views.profile_update_view,     name='api_profile_update'),

    # PATCH /api/users/profile/dashboard-tour-seen/  → 標記 Dashboard 首次導覽已完成
    path('users/profile/dashboard-tour-seen/', views.dashboard_tour_seen_view,
         name='api_dashboard_tour_seen'),

    # ── 密碼管理 ───────────────────────────────────────
    # POST  /api/users/change-password/    → 修改密碼（已登入）
    path('users/change-password/',   views.change_password_view,    name='api_change_password'),

    # POST  /api/users/password-reset/     → 忘記密碼（寄送重設信）
    path('users/password-reset/',    views.password_reset_request_view, name='api_password_reset'),

    # POST  /api/users/password-reset/confirm/  → 重設密碼（點連結後）
    path('users/password-reset/confirm/', views.password_reset_confirm_view,
         name='api_password_reset_confirm'),

    # ── Email 驗證 ──────────────────────────────────────
    # GET   /api/users/verify-email/<token>/   → 驗證 Email（重導至登入頁）
    path('users/verify-email/<str:token>/', views.verify_email_view, name='api_verify_email'),

    # POST  /api/users/resend-verification/    → 重新寄送驗證信
    path('users/resend-verification/', views.resend_verification_view,
         name='api_resend_verification'),

    # ── Google OAuth ────────────────────────────────────
    # POST  /api/users/google-login/           → Google ID Token 換取系統 Token
    path('users/google-login/', views.google_login_view, name='api_google_login'),

    # ── 帳號安全 ───────────────────────────────────────
    # GET   /api/users/login-logs/          → 登入紀錄
    path('users/login-logs/',        views.login_logs_view,         name='api_login_logs'),

    # DELETE /api/users/delete/             → 刪除帳號
    path('users/delete/',            views.delete_account_view,     name='api_delete'),
]

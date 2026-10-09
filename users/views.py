"""
users/views.py
API Views — 對應 Activity Diagram 與 Sequence Diagram 的後端邏輯
"""

import hashlib
import secrets
import logging
from django.contrib.auth import login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .throttles import LoginThrottle, RegisterThrottle, PasswordResetThrottle, ResendVerificationThrottle

from .models import CustomUser, StudentProfile, EmailVerificationToken, LoginLog
from flows.models import Reminder

logger = logging.getLogger(__name__)
from .serializers import (
    RegisterSerializer, LoginSerializer,
    StudentProfileSerializer, UserDetailSerializer,
    UpdateBasicInfoSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer,
)


# ══════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════
def post_login_url(user):
    """
    登入後的落地頁（帳密登入、Google 登入、已登入再進首頁／登入頁共用）。
    superuser → Student Insights；其餘依是否已填個人資料 → Dashboard 或填寫個人資料。
    """
    if user.is_superuser:
        return reverse('insights:dashboard')
    has_profile = hasattr(user, 'student_profile') and user.student_profile is not None
    return reverse('dashboard') if has_profile else reverse('profile_setup')


def get_client_ip(request):
    """取得客戶端 IP。僅在 settings.TRUST_X_FORWARDED_FOR=True 時才讀取 Proxy header。"""
    if getattr(settings, 'TRUST_X_FORWARDED_FOR', False):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def success_response(data=None, message='成功', status_code=200):
    return Response({'success': True, 'message': message, 'data': data or {}},
                    status=status_code)

def error_response(message='發生錯誤', errors=None, status_code=400):
    return Response({'success': False, 'message': message, 'errors': errors or {}},
                    status=status_code)


# ══════════════════════════════════════════
# 1. 註冊 API
# POST /api/users/register/
# Activity Diagram: 進入系統 → 否有帳號 → 註冊帳號 → 填寫基本資料
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterThrottle])
def register_view(request):
    """
    Request Body:
      { "name": "Ahmad", "email": "a@b.com",
        "password": "Password1!", "password2": "Password1!" }

    Response (201):
      { "success": true,
        "user": { "id":1, "name":"Ahmad", "email":"a@b.com", ... },
        "has_profile": false }
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response('資料驗證失敗', serializer.errors, 400)

    user = serializer.save()

    # 寄送 Email 驗證信（可改為 Celery 非同步）
    _send_verification_email(user)

    user_data = UserDetailSerializer(user).data
    return Response({
        'success': True,
        'message': '帳號建立成功，驗證信已寄出',
        'user': user_data,
        'has_profile': False,
    }, status=201)


# ══════════════════════════════════════════
# 2. 登入 API
# POST /api/users/login/
# Activity Diagram: 進入系統 → 是否已有帳號 → 登入
# Sequence Diagram: viewProcessFlow → generatePersonalizedFlow
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login_view(request):
    """
    Request Body:
      { "email": "a@b.com", "password": "Password1!" }

    Response (200):
      { "success": true,
        "user": {...}, "has_profile": true/false }
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        email = request.data.get('email', '')
        failed_user = None
        if email:
            try:
                failed_user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                logger.warning('登入失敗（帳號不存在）: ip=%s email=%s', get_client_ip(request), email)
        _log_login(failed_user, request, success=False)
        return error_response('登入失敗', serializer.errors, 401)

    user  = serializer.validated_data['user']

    # 建立 Django session，讓模板的 user.is_authenticated 與 @login_required 正常運作
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    # 更新最後登入 IP
    ip = get_client_ip(request)
    user.last_login_ip = ip
    user.save(update_fields=['last_login_ip'])

    # 記錄登入日誌
    _log_login(user, request, success=True)

    has_profile = hasattr(user, 'student_profile') and user.student_profile is not None
    user_data   = UserDetailSerializer(user).data

    return success_response({
        'user':  user_data,
        'has_profile': has_profile,
        'redirect_url': post_login_url(user),
    }, '登入成功')


# ══════════════════════════════════════════
# 3. 登出 API
# POST /api/users/logout/
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """清除 Django session"""
    logout(request)
    return success_response(message='登出成功')


# ══════════════════════════════════════════
# 4. 取得當前使用者資料
# GET /api/users/me/
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Response: 完整使用者資料（含 StudentProfile）
    對應 Sequence Diagram: UI 向後端取得 flow + taskList + progressInfo
    """
    serializer = UserDetailSerializer(request.user)
    return success_response(serializer.data)


# ══════════════════════════════════════════
# 5. 建立 / 取得學生資料
# GET  /api/users/profile/
# POST /api/users/profile/setup/
# Activity Diagram: 填寫基本資料 → 選擇國際/身份別/入學狀態
# ══════════════════════════════════════════
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile_setup_view(request):
    """
    GET: 取得現有 Profile
    POST: 初次建立 StudentProfile

    Request Body (POST):
      { "nationality": "Indonesia", "university": "國立臺灣大學",
        "identity_type": "overseas_chinese", "admission_status": "pre_arrival",
        "department": "資訊工程學系", "expected_arrival": "2025-09-01" }
    """
    user = request.user

    if request.method == 'GET':
        if hasattr(user, 'student_profile'):
            return success_response(
                StudentProfileSerializer(user.student_profile).data
            )
        return error_response('尚未建立學生資料', status_code=404)

    # POST: 建立
    if getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False) and not user.email_verified:
        return error_response('請先驗證您的電子信箱才能填寫個人資料', status_code=403)

    if hasattr(user, 'student_profile'):
        return error_response('學生資料已存在，請使用 PATCH /api/users/profile/update/ 更新')

    serializer = StudentProfileSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response('資料驗證失敗', serializer.errors)

    profile = serializer.save(user=user)

    # ── 觸發模塊二：生成個人化流程（預留接口）──
    # from flow.tasks import generate_personalized_flow
    # generate_personalized_flow.delay(user.id)

    return Response({
        'success': True,
        'message': '學生資料建立成功，個人化流程已生成',
        'data': StudentProfileSerializer(profile).data,
    }, status=201)


# ══════════════════════════════════════════
# 6. 更新學生資料
# PATCH /api/users/profile/update/
# ══════════════════════════════════════════
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def profile_update_view(request):
    """
    部分更新使用者基本資料（姓名、國籍、學校等）
    """
    user = request.user
    serializer = UpdateBasicInfoSerializer(data=request.data, partial=True)
    if not serializer.is_valid():
        return error_response('資料驗證失敗', serializer.errors)

    data = serializer.validated_data
    data.pop('university', None)  # 學校與帳號永久綁定，不允許修改
    data.pop('identity_type', None)  # 身份別建立後不允許修改

    # 身份別已鎖定，但國籍 / 問答可改 → 檢查改完後是否與既有身份別矛盾
    if hasattr(user, 'student_profile'):
        from .serializers import validate_identity_consistency
        profile = user.student_profile
        consistency_errors = validate_identity_consistency(
            profile.identity_type,
            data.get('nationality', profile.nationality),
            data.get('has_taiwan_id', profile.has_taiwan_id),
        )
        if consistency_errors:
            return error_response('資料驗證失敗', consistency_errors)

    # 更新 CustomUser.name
    if 'name' in data:
        user.name = data.pop('name')
        user.save(update_fields=['name'])

    # 更新 StudentProfile
    if data and hasattr(user, 'student_profile'):
        profile = user.student_profile
        for field, value in data.items():
            setattr(profile, field, value)
        profile.save()

    return success_response(
        UserDetailSerializer(user).data,
        '個人資料更新成功'
    )


# ══════════════════════════════════════════
# 6b. 標記 Dashboard 首次導覽已完成
# PATCH /api/users/profile/dashboard-tour-seen/
# ══════════════════════════════════════════
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def dashboard_tour_seen_view(request):
    if not hasattr(request.user, 'student_profile'):
        return error_response('尚未建立學生資料', status_code=404)

    profile = request.user.student_profile
    if not profile.has_seen_dashboard_tour:
        profile.has_seen_dashboard_tour = True
        profile.save(update_fields=['has_seen_dashboard_tour'])

    return success_response(message='已標記導覽完成')


# ══════════════════════════════════════════
# 7. 修改密碼
# POST /api/users/change-password/
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Request Body:
      { "old_password": "...", "new_password1": "...", "new_password2": "..." }
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return error_response('密碼修改失敗', serializer.errors)

    request.user.set_password(serializer.validated_data['new_password1'])
    request.user.save()

    return success_response(message='密碼更新成功，請重新登入')


# ══════════════════════════════════════════
# 8. 忘記密碼（寄送重設信）
# POST /api/users/password-reset/
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def password_reset_request_view(request):
    """
    Request Body: { "email": "a@b.com" }
    Response: 無論帳號是否存在，都回傳成功（防止帳號枚舉攻擊）
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response('資料驗證失敗', serializer.errors)

    email = serializer.validated_data['email']
    try:
        user = CustomUser.objects.get(email=email)
        _send_password_reset_email(user)
    except CustomUser.DoesNotExist:
        pass  # 不揭露帳號是否存在

    return success_response(message='若此信箱已註冊，重設連結已寄出')


# ══════════════════════════════════════════
# 9. 重設密碼（點擊連結後）
# POST /api/users/password-reset/confirm/
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def password_reset_confirm_view(request):
    """
    Request Body:
      { "uid": "base64-uid", "token": "reset-token", "new_password": "..." }
    """
    uid   = request.data.get('uid')
    token = request.data.get('token')
    new_pw = request.data.get('new_password', '')

    try:
        user_id = urlsafe_base64_decode(uid).decode()
        user    = CustomUser.objects.get(pk=user_id)
    except (CustomUser.DoesNotExist, ValueError, Exception):
        return error_response('無效的重設連結', status_code=400)

    if not default_token_generator.check_token(user, token):
        return error_response('重設連結已過期或無效', status_code=400)

    try:
        validate_password(new_pw, user)
    except DjangoValidationError as e:
        return error_response('密碼強度不足', {'new_password': list(e.messages)})

    user.set_password(new_pw)
    user.save()
    return success_response(message='密碼重設成功，請重新登入')


# ══════════════════════════════════════════
# 10. Email 驗證
# GET /api/users/verify-email/<token>/
# 點擊信件連結後重導至登入頁（瀏覽器友善）
# ══════════════════════════════════════════
def verify_email_view(request, token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        ev_token = EmailVerificationToken.objects.get(token=token_hash, is_used=False)
    except EmailVerificationToken.DoesNotExist:
        return HttpResponseRedirect('/login/?verified=fail')

    if ev_token.is_expired():
        return HttpResponseRedirect('/login/?verified=expired')

    user = ev_token.user
    user.email_verified = True
    user.save(update_fields=['email_verified'])
    ev_token.is_used = True
    ev_token.save(update_fields=['is_used'])

    return HttpResponseRedirect('/login/?verified=1')


# ══════════════════════════════════════════
# 10b. Google OAuth 登入
# POST /api/users/google-login/
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login_view(request):
    """
    Request Body: { "credential": "<Google ID Token>" }
    驗證 Google ID Token，自動建立或取得對應帳號，並建立登入 session。
    """
    credential = request.data.get('credential')
    if not credential:
        return error_response('缺少 Google 憑證')

    if not settings.GOOGLE_CLIENT_ID:
        return error_response('伺服器尚未設定 Google OAuth', status_code=503)

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except ValueError as e:
        logger.warning('Google ID Token 驗證失敗: %s', e)
        return error_response('Google 憑證無效或已過期', status_code=401)

    email = idinfo.get('email')
    name  = idinfo.get('name') or email.split('@')[0]

    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={'name': name, 'email_verified': True, 'is_active': True},
    )

    if not created:
        if not user.is_active:
            return error_response('此帳號已停用', status_code=403)
        # 若 Google 已驗證 email，同步更新
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=['email_verified'])

    if created:
        user.set_unusable_password()
        user.save()

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    has_profile = hasattr(user, 'student_profile') and user.student_profile is not None
    return success_response({
        'user':        UserDetailSerializer(user).data,
        'has_profile': has_profile,
        'is_new_user': created,
        'redirect_url': post_login_url(user),
    }, '登入成功')


# ══════════════════════════════════════════
# 11. 刪除帳號
# DELETE /api/users/delete/
# ══════════════════════════════════════════
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    """
    軟刪除：將帳號設為 is_active=False
    或硬刪除：user.delete()
    """
    user = request.user
    user.is_active = False
    user.save(update_fields=['is_active'])
    logout(request)  # 同步清除 Django session
    return success_response(message='帳號已停用')


# ══════════════════════════════════════════
# 12. 重新寄送驗證信
# POST /api/users/resend-verification/
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([ResendVerificationThrottle])
def resend_verification_view(request):
    user = request.user
    if user.email_verified:
        return error_response('此信箱已完成驗證')
    _send_verification_email(user)
    return success_response(message='驗證信已重新寄出')


# ══════════════════════════════════════════
# 13. 登入紀錄
# GET /api/users/login-logs/
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def login_logs_view(request):
    logs = LoginLog.objects.filter(user=request.user).order_by('-login_at')[:20]
    data = [
        {
            'ip': log.ip_address,
            'at': log.login_at.strftime('%Y-%m-%d %H:%M'),
            'success': log.success,
        }
        for log in logs
    ]
    return success_response(data)


# ══════════════════════════════════════════
# PRIVATE HELPERS
# ══════════════════════════════════════════
def _send_verification_email(user):
    """產生並寄送 Email 驗證信"""
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    EmailVerificationToken.objects.create(user=user, token=token_hash)
    link = f"{settings.SITE_BASE_URL}/api/users/verify-email/{raw_token}/"
    send_mail(
        subject='【ReadyTo Taiwan】請驗證您的電子信箱',
        message=f'您好 {user.name}，\n\n請點擊以下連結完成驗證：\n{link}\n\n連結有效期限為 24 小時。',
        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@readytotaiwan.tw',
        recipient_list=[user.email],
        fail_silently=True,
    )


def _send_password_reset_email(user):
    """產生並寄送密碼重設信"""
    uid   = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link  = f"{settings.SITE_BASE_URL}/reset-password?uid={uid}&token={token}"
    send_mail(
        subject='【ReadyTo Taiwan】密碼重設申請',
        message=f'您好 {user.name}，\n\n請點擊以下連結重設密碼：\n{link}\n\n若非本人操作，請忽略此信。',
        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@readytotaiwan.tw',
        recipient_list=[user.email],
        fail_silently=True,
    )


def _log_login(user, request, success=True):
    ip = get_client_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:500]
    if user:
        LoginLog.objects.create(user=user, ip_address=ip, user_agent=ua, success=success)
        if not success:
            logger.warning('登入失敗: user=%s ip=%s', user.email, ip)
    else:
        logger.warning('登入失敗（未知使用者）: ip=%s', ip)

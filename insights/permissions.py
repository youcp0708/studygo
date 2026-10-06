"""
insights/permissions.py
Student Insights 的存取控制（規格 §11.1）。

- 系統管理員（role='admin' 或 superuser）：可看全部學校
- 校方人員（有啟用中的 StaffProfile）：只能看所屬學校
- 其他人（包含所有學生）：403
"""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import StaffProfile

ALL_SCHOOLS = 'ALL'


def get_scope(user):
    """回傳 'ALL'、學校代碼，或 None（無權限）。"""
    if not user.is_authenticated:
        return None
    if user.is_superuser or getattr(user, 'role', '') == 'admin':
        return ALL_SCHOOLS
    staff = StaffProfile.objects.filter(user=user, is_active=True).only('university').first()
    return staff.university if staff else None


def insights_access_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url='login_page')
        scope = get_scope(request.user)
        if scope is None:
            raise PermissionDenied
        request.insights_scope = scope
        return view_func(request, *args, **kwargs)
    return wrapper

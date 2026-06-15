"""
users/admin.py
Django Admin 設定 — 系統管理員（Admin 角色）使用
對應 Use Case Diagram：系統管理員功能
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, StudentProfile, LoginLog, EmailVerificationToken


# ══════════════════════════════════════════
# Custom User Admin
# ══════════════════════════════════════════
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    # 列表顯示欄位
    list_display    = ('email', 'name', 'role', 'email_verified', 'is_active', 'date_joined')
    list_filter     = ('role', 'is_active', 'email_verified', 'is_staff')
    search_fields   = ('email', 'name')
    ordering        = ('-date_joined',)

    # 詳細頁分區
    fieldsets = (
        ('帳號資訊',   {'fields': ('email', 'password')}),
        ('個人資料',   {'fields': ('name', 'role')}),
        ('狀態',       {'fields': ('is_active', 'is_staff', 'is_superuser', 'email_verified')}),
        ('安全記錄',   {'fields': ('last_login_ip', 'last_login', 'date_joined')}),
        ('權限',       {'fields': ('groups', 'user_permissions')}),
    )
    readonly_fields = ('last_login', 'date_joined', 'last_login_ip')

    # 新增使用者表單
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2'),
        }),
    )


# ══════════════════════════════════════════
# Student Profile Admin
# ══════════════════════════════════════════
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display   = ('user', 'region', 'nationality', 'university', 'identity_type',
                      'admission_status', 'has_taiwan_id', 'is_deferred', 'created_at')
    list_filter    = ('region', 'nationality', 'identity_type', 'admission_status')
    search_fields  = ('user__name', 'user__email', 'university')
    ordering       = ('-created_at',)
    readonly_fields= ('created_at', 'updated_at')

    # 對應 Use Case：使用者管理帳號、維護資訊內容
    actions = ['mark_as_arrived']

    @admin.action(description='標記為已抵臺就學中')
    def mark_as_arrived(self, request, queryset):
        queryset.update(admission_status='arrived')
        self.message_user(request, f'已更新 {queryset.count()} 筆學生狀態')


# ══════════════════════════════════════════
# Login Log Admin（對應 Use Case：系統管理員查看帳號）
# ══════════════════════════════════════════
@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'ip_address', 'login_at', 'success')
    list_filter   = ('success',)
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'login_at', 'success')
    ordering      = ('-login_at',)

    def has_add_permission(self, request):
        return False  # 不允許手動新增


# ══════════════════════════════════════════
# Email Verification Token Admin
# ══════════════════════════════════════════
@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display  = ('user', 'is_used', 'created_at')
    list_filter   = ('is_used',)
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at')

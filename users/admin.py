"""
users/admin.py
Django Admin 設定 — 系統管理員（Admin 角色）使用
對應 Use Case Diagram：系統管理員功能
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser, StudentProfile, LoginLog, EmailVerificationToken, Department,
    AlumniShare, School, SchoolUnit,
)


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
# Alumni Share Admin（學長姐分享審核 / 下架）
# ══════════════════════════════════════════
@admin.register(AlumniShare)
class AlumniShareAdmin(admin.ModelAdmin):
    list_display  = ('user', 'university', 'nationality', 'program', 'rating', 'is_active', 'created_at')
    list_filter   = ('university', 'rating', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('user__name', 'user__email', 'content', 'program')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at',)


# ══════════════════════════════════════════
# Department Admin（系所清單，供註冊頁下拉選單使用）
# ══════════════════════════════════════════
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ('university', 'faculty', 'name', 'name_en', 'discipline', 'order', 'is_active')
    list_filter   = ('university', 'faculty', 'discipline', 'is_active')
    list_editable = ('discipline', 'order', 'is_active')
    search_fields = ('name', 'name_en', 'faculty')
    ordering      = ('university', 'order')


# ══════════════════════════════════════════
# School Admin（chatbot 校務問答的資料來源）
# last_verified_at 留空或過舊者代表尚未查核，需人工對照官網確認。
# ══════════════════════════════════════════
class SchoolUnitInline(admin.TabularInline):
    model  = SchoolUnit
    extra  = 0
    fields = ('name', 'aliases', 'location', 'tel', 'ext', 'office_hours', 'order', 'is_active')


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display  = ('code', 'name', 'main_tel', 'intl_office_ext', 'last_verified_at', 'is_active')
    list_filter   = ('is_active', 'last_verified_at')
    search_fields = ('code', 'name', 'name_en', 'aliases')
    inlines       = [SchoolUnitInline]
    readonly_fields = ('updated_at',)


@admin.register(SchoolUnit)
class SchoolUnitAdmin(admin.ModelAdmin):
    list_display  = ('school', 'name', 'location', 'tel', 'ext', 'is_active')
    list_filter   = ('school', 'is_active')
    search_fields = ('name', 'name_en', 'aliases', 'location')


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

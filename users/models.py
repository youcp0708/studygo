"""
users/models.py
對應 Class Diagram 中的 Student 與 Admin 類別
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ══════════════════════════════════════════
# CUSTOM USER MANAGER
# ══════════════════════════════════════════
class CustomUserManager(BaseUserManager):
    """以 email 作為唯一識別的 User Manager"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('電子郵件為必填欄位')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


# ══════════════════════════════════════════
# CUSTOM USER MODEL
# 對應 Class Diagram: Student + Admin 的共用帳號層
# ══════════════════════════════════════════
class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    取代 Django 預設 User，以 email 登入。
    對應 Class Diagram Student：studentId, name, email, password
    對應 Class Diagram Admin：adminId, name, email
    """

    ROLE_CHOICES = [
        ('student', '境外學生'),
        ('admin',   '系統管理員'),
    ]

    email       = models.EmailField(unique=True, verbose_name='電子郵件')
    name        = models.CharField(max_length=100, verbose_name='姓名')
    role        = models.CharField(max_length=20, choices=ROLE_CHOICES,
                                   default='student', verbose_name='角色')
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='建立時間')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='最後登入IP')
    email_verified = models.BooleanField(default=False, verbose_name='Email 已驗證')

    objects = CustomUserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name      = '使用者'
        verbose_name_plural = '使用者'
        db_table          = 'users_customuser'

    def __str__(self):
        return f'{self.name} <{self.email}>'

    # ── Class Diagram 方法對應 ──
    def register(self):
        """由 View 層呼叫，建立帳號流程"""
        pass

    def login_user(self, request):
        """登入流程，由 View 層呼叫"""
        pass


# ══════════════════════════════════════════
# STUDENT PROFILE
# 對應 Class Diagram: Student 的詳細資料欄位
# ══════════════════════════════════════════
class StudentProfile(models.Model):
    """
    境外學生基本資料，對應 Class Diagram Student：
    nationality, university, identityType, admissionStatus
    """

    # ── 身份別選項 (identityType) ──
    IDENTITY_CHOICES = [
        ('overseas_chinese_student', '僑生（海外華裔）'),
        ('foreign_student',          '外籍生（一般外國學生）')
    ]

    # ── 入學狀態選項 (admissionStatus) ──
    ADMISSION_STATUS_CHOICES = [
        ('pre_arrival', '入境前準備中'),
        ('arrived',     '已抵臺就學中'),
    ]

    # ── 國籍選項 (nationality) ──
    NATIONALITY_CHOICES = [
        ('Indonesia',    '印尼'),
        ('Malaysia',     '馬來西亞'),
        ('Vietnam',      '越南'),
        ('Thailand',     '泰國'),
        ('Philippines',  '菲律賓'),
        ('Cambodia',     '柬埔寨'),
        ('Myanmar',      '緬甸'),
        ('Japan',        '日本'),
        ('Korea',        '韓國'),
        ('Other',        '其他'),
    ]

    # ── 關聯 CustomUser（一對一）──
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='使用者帳號'
    )

    # ── Class Diagram 欄位 ──
    nationality      = models.CharField(max_length=50, choices=NATIONALITY_CHOICES,
                                        verbose_name='國籍')
    university       = models.CharField(max_length=200, verbose_name='就讀學校')
    identity_type    = models.CharField(max_length=30, choices=IDENTITY_CHOICES,
                                        verbose_name='身份別')
    admission_status = models.CharField(max_length=20, choices=ADMISSION_STATUS_CHOICES,
                                        default='applied', verbose_name='入學狀態')

    # ── 額外資料 ──
    department       = models.CharField(max_length=200, blank=True, verbose_name='系所')
    expected_arrival = models.DateField(null=True, blank=True, verbose_name='預計抵台日期')
    avatar           = models.ImageField(upload_to='avatars/', null=True, blank=True,
                                         verbose_name='頭像')
    preferred_language = models.CharField(max_length=10, default='zh-hant',
                                          verbose_name='慣用語言')

    # ── 時間戳 ──
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True,     verbose_name='更新時間')

    class Meta:
        verbose_name        = '學生資料'
        verbose_name_plural = '學生資料'
        db_table            = 'users_studentprofile'

    def __str__(self):
        return f'{self.user.name} - {self.get_nationality_display()} - {self.get_identity_type_display()}'

    # ── Class Diagram 方法對應 ──
    def store_info(self):
        """儲存個人資料（由 View 層呼叫 save()）"""
        self.save()

    def record_identity(self, identity_type):
        """記錄身份別"""
        self.identity_type = identity_type
        self.save(update_fields=['identity_type'])

    def get_admission_needs(self):
        """根據身份別與狀態回傳所需流程（由 ProcessFlow 使用）"""
        return {
            'nationality':      self.nationality,
            'identity_type':    self.identity_type,
            'admission_status': self.admission_status,
        }


# ══════════════════════════════════════════
# EMAIL VERIFICATION TOKEN
# ══════════════════════════════════════════
class EmailVerificationToken(models.Model):
    """Email 驗證 Token，用於帳號建立後的信箱驗證"""
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_tokens')
    token      = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    class Meta:
        db_table = 'users_emailverificationtoken'

    def is_expired(self):
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=24)


# ══════════════════════════════════════════
# LOGIN LOG（對應 Sequence Diagram 中的登入流程）
# ══════════════════════════════════════════
class LoginLog(models.Model):
    """記錄使用者登入歷程，供「帳號安全 → 登入紀錄」使用"""
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    login_at   = models.DateTimeField(auto_now_add=True)
    success    = models.BooleanField(default=True)

    class Meta:
        db_table  = 'users_loginlog'
        ordering  = ['-login_at']

    def __str__(self):
        return f'{self.user.email} @ {self.login_at:%Y-%m-%d %H:%M}'

"""
users/models.py
對應 Class Diagram 中的 Student 與 Admin 類別
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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
    ('overseas_chinese', _('僑生')),
    ('foreign_student', _('外籍生')),
    ('hong_kong_macau', _('港澳生')),
]

    # ── 入學狀態選項 (admissionStatus) ──
    ADMISSION_STATUS_CHOICES = [
    ('pre_arrival', _('入臺前準備')),
    ('arrived', _('抵臺後')),
]   
    # ── 地區選項 (region) ──
    REGION_CHOICES = [
        ('East Asia', _('東亞')),
        ('Southeast Asia', _('東南亞')),
        ('South Asia', _('南亞')),
        ('Middle East', _('中東')),
        ('Europe', _('歐洲')),
        ('North America', _('北美洲')),
        ('Latin America', _('中南美洲')),
        ('Africa', _('非洲')),
        ('Oceania', _('大洋洲')),
    ]

    # ── 國籍選項 (nationality) ──
    NATIONALITY_CHOICES = [
        # 東亞
        ('Japan',       _('日本')),
        ('Korea',       _('韓國')),
        ('Macau',       _('澳門')),
        ('Hong Kong',   _('香港')),
        ('Mongolia',    _('蒙古')),
        # 東南亞
        ('Indonesia',   _('印尼')),
        ('Malaysia',    _('馬來西亞')),
        ('Vietnam',     _('越南')),
        ('Thailand',    _('泰國')),
        ('Philippines', _('菲律賓')),
        ('Cambodia',    _('柬埔寨')),
        ('Myanmar',     _('緬甸')),
        ('Singapore',   _('新加坡')),
        # 南亞
        ('India',       _('印度')),
        ('Pakistan',    _('巴基斯坦')),
        ('Bangladesh',  _('孟加拉')),
        # 中東
        ('Saudi Arabia',_('沙烏地阿拉伯')),
        ('UAE',         _('阿拉伯聯合大公國')),
        ('Turkey',      _('土耳其')),
        # 歐洲
        ('UK',          _('英國')),
        ('France',      _('法國')),
        ('Germany',     _('德國')),
        ('Italy',       _('義大利')),
        ('Spain',       _('西班牙')),
        # 北美洲
        ('USA',         _('美國')),
        ('Canada',      _('加拿大')),
        # 中南美洲
        ('Brazil',      _('巴西')),
        ('Mexico',      _('墨西哥')),
        ('Argentina',   _('阿根廷')),
        # 非洲
        ('South Africa',_('南非')),
        ('Egypt',       _('埃及')),
        ('Nigeria',     _('奈及利亞')),
        # 大洋洲
        ('Australia',   _('澳洲')),
        ('New Zealand', _('紐西蘭')),
        
        ('Other',       _('其他')),
    ]

    # ── 學校選項 (university) ──
    UNIVERSITY_CHOICES = [
        ('NTU', _('國立臺灣大學（NTU）')),
        ('NCCU', _('國立政治大學（NCCU）')),
        ('NTHU', _('國立清華大學（NTHU）')),
        ('NYCU', _('國立陽明交通大學（NYCU）')),
        ('NCKU', _('國立成功大學（NCKU）')),
        ('NCHU', _('國立中興大學（NCHU）')),
        ('NCU', _('國立中央大學（NCU）')),
        ('NSYSU', _('國立中山大學（NSYSU）')),
        ('NTNU', _('國立臺灣師範大學（NTNU）')),
        ('NTPU', _('國立臺北大學（NTPU）')),
        ('NUTN', _('國立臺南大學（NUTN）')),
        ('NCYU', _('國立嘉義大學（NCYU）')),
        ('NDHU', _('國立東華大學（NDHU）')),
        ('NCNU', _('國立暨南國際大學（NCNU）')),
        ('NIU', _('國立宜蘭大學（NIU）')),
        ('NUU', _('國立聯合大學（NUU）')),
        ('NTTU', _('國立臺東大學（NTTU）')),
        ('NQU', _('國立金門大學（NQU）')),
        ('NPU', _('國立澎湖科技大學（NPU）')),
        ('NTUST', _('國立臺灣科技大學（NTUST）')),
        ('NTUT', _('國立臺北科技大學（NTUT）')),
        ('NKUST', _('國立高雄科技大學（NKUST）')),
        ('YunTech', _('國立雲林科技大學（YunTech）')),
        ('NPUST', _('國立屏東科技大學（NPUST）')),
        ('NTCUST', _('國立臺中科技大學（NTCUST）')),
        ('NFU', _('國立虎尾科技大學（NFU）')),
        ('NKUHT', _('國立高雄餐旅大學（NKUHT）')),
        ('NKNU', _('國立高雄師範大學（NKNU）')),
        ('NCUE', _('國立彰化師範大學（NCUE）')),
        ('NTUE', _('國立臺北教育大學（NTUE）')),
        ('NTCU', _('國立臺中教育大學（NTCU）')),
        ('NPTU', _('國立屏東大學（NPTU）')),
        ('NTUS', _('國立臺灣體育運動大學（NTUS）')),
        ('NTUB', _('國立臺北商業大學（NTUB）')),
        ('NOU', _('國立空中大學（NOU）')),
        ('Other', _('其他（Other）')),
    ]

    # ── 關聯 CustomUser（一對一）──
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='使用者帳號'
    )

    # ── Class Diagram 欄位 ──
    region           = models.CharField(max_length=50, choices=REGION_CHOICES,
                                        blank=True, null=True, verbose_name='所屬地區')
    nationality      = models.CharField(max_length=50, choices=NATIONALITY_CHOICES,
                                        verbose_name='國籍')
    university       = models.CharField(max_length=200, choices=UNIVERSITY_CHOICES, verbose_name='就讀學校')
    identity_type    = models.CharField(max_length=30, choices=IDENTITY_CHOICES,
                                        verbose_name='身份別')
    admission_status = models.CharField(max_length=20, choices=ADMISSION_STATUS_CHOICES,
                                        default='pre_arrival', verbose_name='入學狀態')

    # ── 額外資料 ──
    department       = models.CharField(max_length=200, blank=True, verbose_name='系所')
    expected_arrival = models.DateField(null=True, blank=True, verbose_name='預計抵台日期')
    avatar           = models.ImageField(upload_to='avatars/', null=True, blank=True,
                                         verbose_name='頭像')
    preferred_language = models.CharField(max_length=10, default='zh-hant',
                                          verbose_name='慣用語言')

    # ── 問答區域欄位（供後續流程模塊使用）──
    has_taiwan_id = models.BooleanField(null=True, blank=True, verbose_name='是否擁有台灣身份證')
    is_deferred   = models.BooleanField(null=True, blank=True, verbose_name='是否延遲入學')
    # has_indo_prep = models.BooleanField(null=True, blank=True, verbose_name='是否上印輔班')

    

    # ── 時間戳 ──
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True,     verbose_name='更新時間')

    class Meta:
        verbose_name        = '學生資料'
        verbose_name_plural = '學生資料'
        db_table            = 'users_studentprofile'

    def __str__(self):
        return self.user.name if self.user.name else self.user.email

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
# 18 學群分類（台灣大考中心 / 升學輔導通用分類）
# 供「系所 → 學群」對應，AI 小老師依學群載入對應課業知識
# ══════════════════════════════════════════
DISCIPLINE_CHOICES = [
    ('info',             '資訊學群'),
    ('engineering',      '工程學群'),
    ('math_science',     '數理化學群'),
    ('medical',          '醫藥衛生學群'),
    ('life_science',     '生命科學學群'),
    ('bio_resource',     '生物資源學群'),
    ('earth_env',        '地球與環境學群'),
    ('architecture',     '建築與設計學群'),
    ('arts',             '藝術學群'),
    ('social_psy',       '社會與心理學群'),
    ('mass_comm',        '大眾傳播學群'),
    ('foreign_lang',     '外語學群'),
    ('humanities',       '文史哲學群'),
    ('education',        '教育學群'),
    ('law_politics',     '法政學群'),
    ('management',       '管理學群'),
    ('finance',          '財經學群'),
    ('recreation_sport', '遊憩與運動學群'),
]


# ══════════════════════════════════════════
# DEPARTMENT（系所）
# 供註冊「填寫個人資料」頁的系所下拉選單使用，
# 由 Django Admin 管理，不再寫死在前端模板。
# ══════════════════════════════════════════
class Department(models.Model):
    university = models.CharField(
        max_length=200,
        choices=StudentProfile.UNIVERSITY_CHOICES,
        verbose_name='所屬學校',
    )
    faculty    = models.CharField(max_length=100, blank=True, verbose_name='學院')
    faculty_en = models.CharField(max_length=100, blank=True, verbose_name='學院 English')
    name       = models.CharField(max_length=200, verbose_name='系所名稱')
    name_en    = models.CharField(max_length=200, blank=True, verbose_name='系所名稱 English')
    discipline = models.CharField(
        max_length=30, choices=DISCIPLINE_CHOICES, blank=True,
        verbose_name='所屬學群',
        help_text='AI 小老師會依此學群載入對應的課業輔導知識',
    )
    order      = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active  = models.BooleanField(default=True, verbose_name='是否啟用')

    class Meta:
        db_table = 'users_department'
        ordering = ['university', 'order', 'id']
        verbose_name = '系所'
        verbose_name_plural = '系所'

    def __str__(self):
        return f'{self.university} - {self.name}'

    def get_localized_name(self, lang_code):
        """系所名稱本地化：非中文語系優先顯示英文，沒填英文則回中文。"""
        if lang_code and not lang_code.startswith('zh') and self.name_en.strip():
            return self.name_en
        return self.name

    def get_localized_faculty(self, lang_code):
        if lang_code and not lang_code.startswith('zh') and self.faculty_en.strip():
            return self.faculty_en
        return self.faculty


# ══════════════════════════════════════════
# SCHOOL（學校基本資料）
# UNIVERSITY_CHOICES 只有代碼與顯示名稱，chatbot 需要地址、總機、
# 國際處分機、行事曆等實際校務資訊才能回答「我的學校」相關問題。
# ══════════════════════════════════════════
class School(models.Model):
    code = models.CharField(
        max_length=200,
        choices=StudentProfile.UNIVERSITY_CHOICES,
        unique=True,
        verbose_name='學校代碼',
    )
    name    = models.CharField(max_length=200, verbose_name='學校全名')
    name_en = models.CharField(max_length=200, blank=True, verbose_name='學校英文全名')
    aliases = models.CharField(
        max_length=500, blank=True,
        verbose_name='簡稱 / 別名',
        help_text='以逗號分隔，學生可能使用的所有稱呼，例如：中央,中大,NCU,中央大學,National Central University',
    )

    address  = models.CharField(max_length=300, blank=True, verbose_name='校本部地址')
    main_tel = models.CharField(max_length=50, blank=True, verbose_name='學校總機')
    website  = models.URLField(blank=True, verbose_name='官方網站')

    intl_office_name = models.CharField(
        max_length=100, blank=True, verbose_name='國際事務處名稱',
        help_text='各校名稱不同，例如：國際事務處 / 國際處 / 國際學生事務組',
    )
    intl_office_tel = models.CharField(max_length=50, blank=True, verbose_name='國際處電話')
    intl_office_ext = models.CharField(max_length=20, blank=True, verbose_name='國際處分機')
    intl_office_url = models.URLField(blank=True, verbose_name='國際處網站')

    calendar_url   = models.URLField(blank=True, verbose_name='行事曆網址')
    admission_url  = models.URLField(blank=True, verbose_name='境外生招生 / 入學申請網址')

    last_verified_at = models.DateField(
        null=True, blank=True,
        verbose_name='最後查核日期',
        help_text='最後一次對照官網確認此資料仍正確的日期，留空代表尚未查核',
    )
    is_active  = models.BooleanField(default=True, verbose_name='是否啟用')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        db_table = 'users_school'
        ordering = ['code']
        verbose_name = '學校資料'
        verbose_name_plural = '學校資料'

    def __str__(self):
        return f'{self.code} - {self.name}'

    def alias_list(self):
        """回傳去空白後的別名清單，供 chatbot 比對學生口語中的學校稱呼。"""
        return [a.strip() for a in self.aliases.split(',') if a.strip()]

    def get_localized_name(self, lang_code):
        if lang_code and not lang_code.startswith('zh') and self.name_en.strip():
            return self.name_en
        return self.name


class SchoolUnit(models.Model):
    """
    校內單位（校長室、國際處、註冊組、宿舍組…）的位置與聯絡方式。
    學生問「校長室在哪裡」時，chatbot 依個人資料的學校找出該校對應單位回答。
    """

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='units',
        verbose_name='所屬學校',
    )
    name    = models.CharField(max_length=100, verbose_name='單位名稱')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='單位英文名稱')
    aliases = models.CharField(
        max_length=300, blank=True,
        verbose_name='別名',
        help_text='以逗號分隔，例如：校長室,校長辦公室,President Office',
    )

    location     = models.CharField(max_length=200, blank=True, verbose_name='位置',
                                    help_text='例如：行政大樓 2 樓 201 室')
    tel          = models.CharField(max_length=50, blank=True, verbose_name='電話')
    ext          = models.CharField(max_length=20, blank=True, verbose_name='分機')
    email        = models.EmailField(blank=True, verbose_name='電子郵件')
    url          = models.URLField(blank=True, verbose_name='單位網頁')
    office_hours = models.CharField(max_length=200, blank=True, verbose_name='服務時間')

    order     = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否啟用')

    class Meta:
        db_table = 'users_school_unit'
        ordering = ['school', 'order', 'id']
        verbose_name = '校內單位'
        verbose_name_plural = '校內單位'

    def __str__(self):
        return f'{self.school.code} - {self.name}'

    def alias_list(self):
        return [a.strip() for a in self.aliases.split(',') if a.strip()]


# ══════════════════════════════════════════
# ALUMNI SHARE（學長姐分享）
# 學生發佈留學經驗分享；分享頁分「我的學校」與「所有學校」兩區，
# 同一篇分享會同時出現在自己學校區與所有學校區。
# ══════════════════════════════════════════
class AlumniShare(models.Model):
    RATING_CHOICES = [(i, '★' * i) for i in range(1, 6)]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='alumni_shares',
        verbose_name='發佈者',
    )
    # 發佈當下從 StudentProfile 快照，之後改個人資料不影響已發佈的分享
    university  = models.CharField(max_length=200, choices=StudentProfile.UNIVERSITY_CHOICES,
                                   verbose_name='學校')
    nationality = models.CharField(max_length=50, choices=StudentProfile.NATIONALITY_CHOICES,
                                   blank=True, verbose_name='國籍')
    program     = models.CharField(max_length=200, blank=True, verbose_name='就讀系所 / 學程')
    title       = models.CharField(max_length=200, blank=True, verbose_name='標題')
    content     = models.TextField(max_length=1000, verbose_name='分享內容')
    rating      = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5,
                                                   verbose_name='推薦指數')
    is_active   = models.BooleanField(default=True, verbose_name='是否顯示',
                                      help_text='管理員可取消勾選以下架不當內容')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='發佈時間')

    class Meta:
        db_table = 'users_alumni_share'
        ordering = ['-created_at']
        verbose_name = '學長姐分享'
        verbose_name_plural = '學長姐分享'

    def __str__(self):
        return f'{self.user.name} ({self.university}) - {self.content[:30]}'

    @property
    def stars(self):
        return '★' * self.rating + '☆' * (5 - self.rating)


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

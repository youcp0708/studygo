"""
chatbot/models.py
AI 聊天機器人模組：儲存每位學生自己的對話紀錄。
"""

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from users.models import DISCIPLINE_CHOICES, StudentProfile

ALLOWED_ATTACHMENT_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'txt', 'csv', 'md', 'json', 'docx', 'xlsx']


class ChatSession(models.Model):
    """一位使用者可有多個聊天對話。"""

    AI_MODE_CHOICES = [
        ("helper", "ReadyTo 任務小幫手"),
        ("friend", "ReadyTo 聊天好朋友"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions"
    )

    title = models.CharField(max_length=100, default="新的聊天")
    ai_mode = models.CharField(
        max_length=20,
        choices=AI_MODE_CHOICES,
        default="helper",
        verbose_name="AI 模式"
    )

    is_pinned = models.BooleanField(
        default=False,
        verbose_name='是否釘選'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='建立時間'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新時間'
    )


    class Meta:
        db_table = 'chatbot_chatsession'
        ordering = ['-is_pinned', '-updated_at']
        verbose_name = '聊天對話'
        verbose_name_plural = '聊天對話'

    def __str__(self):
        return f'{self.user} - {self.title}'


class ChatMessage(models.Model):
    """儲存使用者與 AI 的每一則訊息。"""

    ROLE_CHOICES = [
        ('user', '使用者'),
        ('assistant', 'AI 小幫手'),
        ('system', '系統'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='所屬對話',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='角色')
    content = models.TextField(verbose_name='訊息內容')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='建立時間')

    class Meta:
        db_table = 'chatbot_chatmessage'
        ordering = ['created_at']
        verbose_name = '聊天訊息'
        verbose_name_plural = '聊天訊息'

    def __str__(self):
        return f'{self.get_role_display()}: {self.content[:30]}'


class ChatAttachment(models.Model):
    """聊天訊息附件：檔案、圖片、拍照圖片。"""

    ATTACHMENT_TYPE_CHOICES = [
        ('file', '檔案'),
        ('image', '圖片'),
        ('camera', '拍照'),
    ]

    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='所屬訊息',
    )

    file = models.FileField(
        upload_to='chatbot_uploads/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_ATTACHMENT_EXTENSIONS)],
        verbose_name='附件檔案',
    )

    attachment_type = models.CharField(
        max_length=20,
        choices=ATTACHMENT_TYPE_CHOICES,
        default='file',
        verbose_name='附件類型',
    )

    original_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='原始檔名',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='建立時間',
    )

    class Meta:
        db_table = 'chatbot_attachment'
        verbose_name = '聊天附件'
        verbose_name_plural = '聊天附件'

    def __str__(self):
        return self.original_name or str(self.file)


class ChatFeedback(models.Model):
    """
    學生對 AI 回覆的評價（👍 / 👎）。
    管理者可在後台分析：哪些問題答不好 → 知識庫該補哪些內容（回饋閉環）。
    """

    RATING_CHOICES = [
        ('up',   '👍 有幫助'),
        ('down', '👎 沒幫助'),
    ]

    message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name='被評價的訊息',
    )
    rating = models.CharField(
        max_length=10,
        choices=RATING_CHOICES,
        verbose_name='評價',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        db_table = 'chatbot_feedback'
        ordering = ['-created_at']
        verbose_name = 'AI 回覆評價'
        verbose_name_plural = 'AI 回覆評價'

    def __str__(self):
        return f'{self.get_rating_display()} - {self.message.content[:30]}'


class ChatKnowledge(models.Model):
    """聊天機器人知識庫 / FAQ：給 AI 一般回答參考，可支援多語言。"""

    CATEGORY_CHOICES = [
    # 學校綜合資訊：校區位置、聯絡方式、國際處、行事曆、校內單位、學校特色等
    # 凡是「跟某一所學校有關」的內容都放這裡，並在 university 欄位指定學校
    ('school_info', '學校資訊'),

    ('admission', '入學申請'),
    ('documents', '文件準備'),
    ('document_verification', '文件驗證'),
    ('visa', '簽證'),
    ('financial_proof', '財力證明'),
    ('language_proof', '語言證明'),
    ('before_arrival', '來台前準備'),
    ('entry', '入境規定'),
    ('country_difference', '國家差異'),
    ('identity_type', '身分別流程'),

    ('arrival_transport', '到校交通'),
    ('orientation', '新生報到'),
    ('registration_payment', '註冊繳費'),
    ('student_id', '學生證'),
    ('arc', '居留證 ARC'),
    ('health_check', '健檢'),
    ('insurance', '保險'),
    ('bank', '銀行開戶'),
    ('phone', '手機門號'),
    ('school_system', '校內系統'),

    ('course', '課務選課'),
    ('student_status', '學籍'),
    ('grades', '成績'),
    ('graduation', '畢業'),
    ('dorm', '宿舍'),
    ('renting', '租屋'),
    ('nhi', '健保'),
    ('work_permit', '工作證'),
    ('scholarship', '獎助學金'),
    ('campus_activity', '校內活動'),

    ('library', '圖書館'),
    ('internship', '交換與實習'),
    ('admin_documents', '行政文件'),
    ('transportation', '交通'),
    ('food', '飲食'),
    ('medical', '醫療'),
    ('mental_support', '心理支持'),
    ('emergency', '緊急聯絡'),
    ('living_cost', '生活費'),
    ('other', '其他'),

    ]

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='分類',
    )

    # 學群標籤：留空＝不分學群（所有人適用）；
    # 有值時，AI 小老師會依學生系所對應的學群優先載入這些知識
    discipline = models.CharField(
        max_length=30,
        choices=DISCIPLINE_CHOICES,
        blank=True,
        default='',
        verbose_name='適用學群',
        help_text='對應學生系所的 18 學群分類，留空表示不分學群',
    )

    # 以下三個「適用對象」欄位一律留空＝通用內容，所有學生都會檢索到；
    # 有值時，只有個人資料相符的學生才會檢索到這筆。
    # 例：入學申請各校不同 → 填 university；簽證各國不同 → 填 country。
    university = models.CharField(
        max_length=200,
        choices=StudentProfile.UNIVERSITY_CHOICES,
        blank=True,
        default='',
        verbose_name='適用學校',
        help_text='留空表示所有學校通用；各校做法不同的內容（入學申請、註冊繳費等）請指定學校',
    )

    country = models.CharField(
        max_length=50,
        choices=StudentProfile.NATIONALITY_CHOICES,
        blank=True,
        default='',
        verbose_name='適用國籍',
        help_text='留空表示所有國籍通用；各國做法不同的內容（簽證辦理）請指定國籍',
    )

    identity_type = models.CharField(
        max_length=30,
        choices=StudentProfile.IDENTITY_CHOICES,
        blank=True,
        default='',
        verbose_name='適用身分別',
        help_text='留空表示僑生／外籍生／港澳生皆適用；管道不同的內容請指定身分別',
    )

    title = models.CharField(max_length=200, verbose_name='繁體中文標題')
    title_en = models.CharField(max_length=200, blank=True, verbose_name='英文標題')
    title_vi = models.CharField(max_length=200, blank=True, verbose_name='越文標題')
    title_my = models.CharField(max_length=200, blank=True, verbose_name='緬文標題')
    title_id = models.CharField(max_length=200, blank=True, verbose_name='印尼文標題')
    title_ms = models.CharField(max_length=200, blank=True, verbose_name='馬來文標題')
    title_th = models.CharField(max_length=200, blank=True, verbose_name='泰文標題')
    title_ja = models.CharField(max_length=200, blank=True, verbose_name='日文標題')
    title_ko = models.CharField(max_length=200, blank=True, verbose_name='韓文標題')

    BOT_TYPE_CHOICES = [
    ("helper", "ReadyTo 任務小幫手"),
    ("friend", "ReadyTo 聊天好朋友"),
    ("both", "兩者都可使用"),
]

    bot_type = models.CharField(
        max_length=20,
        choices=BOT_TYPE_CHOICES,
        default="helper",
        verbose_name="適用 AI"
    )

    keywords = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='關鍵字，建議放中文與英文，例如：居留證, ARC, residence permit',
    )

    content = models.TextField(verbose_name='繁體中文內容')
    content_en = models.TextField(blank=True, verbose_name='英文內容')
    content_vi = models.TextField(blank=True, verbose_name='越文內容')
    content_my = models.TextField(blank=True, verbose_name='緬文內容')
    content_id = models.TextField(blank=True, verbose_name='印尼文內容')
    content_ms = models.TextField(blank=True, verbose_name='馬來文內容')
    content_th = models.TextField(blank=True, verbose_name='泰文內容')
    content_ja = models.TextField(blank=True, verbose_name='日文內容')
    content_ko = models.TextField(blank=True, verbose_name='韓文內容')

    source_url = models.URLField(
        blank=True,
        verbose_name='官方來源連結',
        help_text='此知識的官方出處（移民署 / 學校公告等），會附在 AI 回答後供學生查證',
    )
    last_verified_at = models.DateField(
        null=True, blank=True,
        verbose_name='最後查核日期',
        help_text='管理員最後一次確認此內容仍正確的日期',
    )

    is_active = models.BooleanField(default=True, verbose_name='是否啟用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        db_table = 'chatbot_knowledge'
        ordering = ['category', '-updated_at']
        verbose_name = 'Chatbot 知識庫 / FAQ'
        verbose_name_plural = 'Chatbot 知識庫 / FAQ'

    def __str__(self):
        return self.title

    def get_title_by_lang(self, lang_code):
        lang_map = {
            'en': self.title_en,
            'vi': self.title_vi,
            'my': self.title_my,
            'id': self.title_id,
            'ms': self.title_ms,
            'th': self.title_th,
            'ja': self.title_ja,
            'ko': self.title_ko,
        }
        return lang_map.get((lang_code or '').lower(), '') or self.title

    def get_content_by_lang(self, lang_code):
        lang_map = {
            'en': self.content_en,
            'vi': self.content_vi,
            'my': self.content_my,
            'id': self.content_id,
            'ms': self.content_ms,
            'th': self.content_th,
            'ja': self.content_ja,
            'ko': self.content_ko,
        }
        return lang_map.get((lang_code or '').lower(), '') or self.content
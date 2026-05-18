"""
chatbot/models.py
AI 聊天機器人模組：儲存每位學生自己的對話紀錄。
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class ChatSession(models.Model):
    """一位使用者可有多個聊天對話。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        verbose_name='使用者',
    )

    title = models.CharField(
        max_length=120,
        default='新的對話',
        verbose_name='對話標題'
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


class ChatKnowledge(models.Model):
    """聊天機器人知識庫 / FAQ：給 AI 一般回答參考，可支援多語言。"""

    CATEGORY_CHOICES = [
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

    title = models.CharField(max_length=200, verbose_name='繁體中文標題')
    title_en = models.CharField(max_length=200, blank=True, verbose_name='英文標題')
    title_vi = models.CharField(max_length=200, blank=True, verbose_name='越文標題')
    title_my = models.CharField(max_length=200, blank=True, verbose_name='緬文標題')
    title_id = models.CharField(max_length=200, blank=True, verbose_name='印尼文標題')
    title_ms = models.CharField(max_length=200, blank=True, verbose_name='馬來文標題')
    title_th = models.CharField(max_length=200, blank=True, verbose_name='泰文標題')
    title_ja = models.CharField(max_length=200, blank=True, verbose_name='日文標題')
    title_ko = models.CharField(max_length=200, blank=True, verbose_name='韓文標題')

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
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
    title = models.CharField(max_length=120, default='新的對話', verbose_name='對話標題')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        db_table = 'chatbot_chatsession'
        ordering = ['-updated_at']
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

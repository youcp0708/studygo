"""
chatbot/admin.py
後台查看 AI 聊天紀錄，方便展示與除錯。
"""

from django.contrib import admin
from .models import ChatSession, ChatMessage, ChatAttachment, ChatKnowledge, ChatFeedback


class ChatAttachmentInline(admin.TabularInline):
    model = ChatAttachment
    extra = 0
    readonly_fields = ('file', 'attachment_type', 'original_name', 'created_at')
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_pinned', 'created_at', 'updated_at')
    list_filter = ('is_pinned', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__name', 'title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'short_content', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'session__title', 'session__user__email', 'session__user__name')
    readonly_fields = ('session', 'role', 'content', 'created_at')

    def short_content(self, obj):
        return obj.content[:60]
    short_content.short_description = '內容摘要'

    def has_add_permission(self, request):
        return False


@admin.register(ChatFeedback)
class ChatFeedbackAdmin(admin.ModelAdmin):
    """回饋閉環：從 👎 訊息找出知識庫缺口，決定該補哪些內容"""
    list_display = ('id', 'rating', 'user_email', 'message_snippet', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('message__content', 'message__session__user__email')
    readonly_fields = ('message', 'rating', 'created_at', 'updated_at')

    def user_email(self, obj):
        return obj.message.session.user.email
    user_email.short_description = '學生'

    def message_snippet(self, obj):
        return obj.message.content[:60]
    message_snippet.short_description = 'AI 回覆摘要'

    def has_add_permission(self, request):
        return False


@admin.register(ChatKnowledge)
class ChatKnowledgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'university', 'country', 'identity_type', 'discipline', 'source_url', 'last_verified_at', 'is_active', 'updated_at')
    list_filter = ('category', 'university', 'country', 'identity_type', 'discipline', 'is_active', 'updated_at', 'last_verified_at')
    search_fields = (
        'title', 'title_en', 'title_my', 'title_id', 'title_ms', 'title_th', 'title_ja','title_ko','title_vi',
        'keywords',
        'content', 'content_en', 'content_my', 'content_id', 'content_ms', 'content_th', 'content_ja','content_ko','content_vi',
    )
    readonly_fields = ('created_at', 'updated_at')


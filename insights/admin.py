from django.contrib import admin

from .models import InsightAskLog, QuestionClassification, StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'university', 'title', 'powerbi_upn', 'is_active', 'created_at')
    list_filter = ('university', 'is_active')
    search_fields = ('user__email', 'user__name', 'powerbi_upn')
    autocomplete_fields = ('user',)


@admin.register(QuestionClassification)
class QuestionClassificationAdmin(admin.ModelAdmin):
    # 只顯示分類結果，不顯示提問原文
    list_display = ('message_id', 'category', 'method', 'classified_at')
    list_filter = ('category', 'method')
    readonly_fields = ('message', 'category', 'method', 'classified_at')

    def has_add_permission(self, request):
        return False


@admin.register(InsightAskLog)
class InsightAskLogAdmin(admin.ModelAdmin):
    """AI 資料助理問答紀錄：只供稽核，不可新增或修改。"""
    list_display = ('created_at', 'user', 'scope', 'source', 'verified', 'question')
    list_filter = ('source', 'verified', 'scope')
    search_fields = ('user__email', 'question')
    readonly_fields = ('user', 'scope', 'question', 'tool_calls', 'answer', 'source', 'verified', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

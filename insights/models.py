"""
insights/models.py
Student Insights 的資料表。

分成三類：
1. StaffProfile            ── 校方人員與學校的對應（權限用）
2. QuestionClassification  ── AI 提問的分類結果（原文留在 chatbot，不複製）
3. insights_* 分析表        ── build_insights 每日重建，已去識別化；
                              Dashboard 與 Microsoft Fabric 都只讀這些表
"""

from django.conf import settings
from django.db import models

from chatbot.models import ChatMessage
from users.models import StudentProfile

from .question_categories import QUESTION_CATEGORY_CHOICES
from .task_categories import TASK_CATEGORY_CHOICES


# ══════════════════════════════════════════
# 權限
# ══════════════════════════════════════════
class StaffProfile(models.Model):
    """校方人員（國際處、境外生組…）。只能看所屬學校的聚合資料。"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='insights_staff_profile',
        verbose_name='帳號',
    )
    university = models.CharField(
        max_length=200,
        choices=StudentProfile.UNIVERSITY_CHOICES,
        verbose_name='所屬學校',
    )
    title = models.CharField(max_length=100, blank=True, verbose_name='職稱')
    powerbi_upn = models.EmailField(
        blank=True,
        verbose_name='Power BI 登入帳號',
        help_text='此人登入 Power BI 使用的學校 Microsoft 帳號（UPN），用於 Power BI 列層級安全性（RLS）。',
    )
    is_active = models.BooleanField(default=True, verbose_name='是否啟用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')

    class Meta:
        db_table = 'insights_staff_profile'
        verbose_name = '校方人員'
        verbose_name_plural = '校方人員'

    def __str__(self):
        return f'{self.user} ({self.university})'


# ══════════════════════════════════════════
# AI 提問分類
# ══════════════════════════════════════════
class QuestionClassification(models.Model):
    METHOD_CHOICES = [
        ('rule', '關鍵字規則'),
        ('llm', 'LLM'),
        ('none', '未分類'),
    ]

    message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='insights_classification',
        verbose_name='提問訊息',
    )
    category = models.CharField(max_length=30, choices=QUESTION_CATEGORY_CHOICES, verbose_name='分類')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, verbose_name='分類方式')
    classified_at = models.DateTimeField(auto_now_add=True, verbose_name='分類時間')

    class Meta:
        db_table = 'insights_question_classification'
        verbose_name = 'AI 提問分類'
        verbose_name_plural = 'AI 提問分類'


# ══════════════════════════════════════════
# AI 資料助理問答紀錄
# ══════════════════════════════════════════
class InsightAskLog(models.Model):
    """每次 AI 資料助理問答一筆，用於稽核與成本追蹤（規格 §8.2、§12.3）。"""
    SOURCE_CHOICES = [
        ('llm', 'AI 回答'),
        ('preset', '預設問題卡片'),
        ('error', '失敗'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='insights_ask_logs',
        verbose_name='提問者',
    )
    scope = models.CharField(max_length=200, verbose_name='權限範圍', help_text='學校代碼或 ALL')
    question = models.TextField(verbose_name='問題')
    tool_calls = models.JSONField(default=list, verbose_name='工具呼叫與結果')
    answer = models.TextField(blank=True, verbose_name='回答')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, verbose_name='來源')
    verified = models.BooleanField(default=True, verbose_name='數字已驗證',
                                   help_text='回答中的數字是否都能在工具結果中找到')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='提問時間')

    class Meta:
        db_table = 'insights_ask_log'
        ordering = ['-created_at']
        verbose_name = 'AI 資料助理紀錄'
        verbose_name_plural = 'AI 資料助理紀錄'


# ══════════════════════════════════════════
# 分析表（去識別化，Dashboard 與 AI 資料助理只讀這些）
# 不可加入：姓名、Email、IP、大頭照、系所、聊天原文、任務備註
# ══════════════════════════════════════════
class _AnalyticsBase(models.Model):
    snapshot_date = models.DateField(verbose_name='資料日期')
    is_demo = models.BooleanField(default=False, db_index=True, verbose_name='模擬資料')

    class Meta:
        abstract = True


class _StudentDimensions(models.Model):
    student_key = models.CharField(max_length=32, db_index=True, verbose_name='學生代碼（雜湊）')
    university = models.CharField(max_length=200, db_index=True, verbose_name='學校')
    nationality = models.CharField(max_length=50, verbose_name='國籍')
    region = models.CharField(max_length=50, blank=True, verbose_name='地區')
    identity_type = models.CharField(max_length=30, verbose_name='身份別')
    arrival_cohort = models.CharField(max_length=7, blank=True, verbose_name='抵台梯次', help_text='例：2026-09；空白＝未填抵台日')
    academic_year = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='學年度', help_text='民國年，例：115')

    class Meta:
        abstract = True


class DimStudent(_AnalyticsBase, _StudentDimensions):
    """每位學生一列，用於計算各族群人數。"""
    admission_status = models.CharField(max_length=20, verbose_name='入學狀態')
    preferred_language = models.CharField(max_length=10, blank=True, verbose_name='偏好語言')

    class Meta:
        db_table = 'insights_dim_student'
        verbose_name = '分析表：學生'
        verbose_name_plural = '分析表：學生'


class FactStudentTask(_AnalyticsBase, _StudentDimensions):
    """一筆 StudentTask 一列。is_due / is_overdue 等旗標由 ETL 算好，Power BI 直接加總即可。"""
    task_category = models.CharField(max_length=30, choices=TASK_CATEGORY_CHOICES, verbose_name='任務分類')
    is_required = models.BooleanField(verbose_name='必做')
    has_deadline = models.BooleanField(verbose_name='有截止日')
    due_date = models.DateField(null=True, blank=True, verbose_name='截止日')
    status = models.CharField(max_length=20, verbose_name='完成狀態')
    completed_date = models.DateField(null=True, blank=True, verbose_name='完成日期')
    is_completed = models.BooleanField(verbose_name='已完成')
    is_due = models.BooleanField(verbose_name='已到期', help_text='截止日 ≤ 資料日期')
    is_overdue_open = models.BooleanField(verbose_name='逾期未完成')
    is_overdue_late = models.BooleanField(verbose_name='逾期完成')
    is_overdue = models.BooleanField(verbose_name='逾期')
    is_possibly_unreported = models.BooleanField(verbose_name='可能未回報')
    reminder_count = models.PositiveSmallIntegerField(default=0, verbose_name='到期前提醒次數')

    class Meta:
        db_table = 'insights_fact_student_task'
        verbose_name = '分析表：學生任務'
        verbose_name_plural = '分析表：學生任務'


class FactQuestion(_AnalyticsBase, _StudentDimensions):
    """一則已分類的學生提問一列（不含原文）。"""
    category = models.CharField(max_length=30, choices=QUESTION_CATEGORY_CHOICES, verbose_name='提問分類')
    asked_date = models.DateField(verbose_name='提問日期')

    class Meta:
        db_table = 'insights_fact_question'
        verbose_name = '分析表：學生提問'
        verbose_name_plural = '分析表：學生提問'


class InsightAlert(_AnalyticsBase):
    """風險預警。university='ALL' 代表跨校彙總（只有系統管理員看得到）。"""
    BASELINE_CHOICES = [
        ('yoy', '前一學年度'),
        ('cohort', '上一個抵台梯次'),
        ('group', '整體平均'),
    ]

    university = models.CharField(max_length=200, db_index=True, verbose_name='學校')
    task_category = models.CharField(max_length=30, choices=TASK_CATEGORY_CHOICES, verbose_name='任務分類')
    baseline_type = models.CharField(max_length=10, choices=BASELINE_CHOICES, verbose_name='比較基準')
    current_label = models.CharField(max_length=60, verbose_name='目前期間／族群')
    current_rate = models.FloatField(verbose_name='目前逾期率')
    current_n = models.PositiveIntegerField(verbose_name='目前分母')
    baseline_label = models.CharField(max_length=60, verbose_name='比較基準期間／族群')
    baseline_rate = models.FloatField(verbose_name='基準逾期率')
    baseline_n = models.PositiveIntegerField(verbose_name='基準分母')
    delta_pp = models.FloatField(verbose_name='變化（百分點）')
    concentrated_groups = models.JSONField(default=list, verbose_name='逾期集中族群')
    reminder_effect = models.JSONField(default=dict, verbose_name='提醒成效參考')
    recommendation = models.TextField(verbose_name='行動建議')

    class Meta:
        db_table = 'insights_alert'
        ordering = ['-delta_pp']
        verbose_name = '分析表：風險預警'
        verbose_name_plural = '分析表：風險預警'


class StaffAccess(_AnalyticsBase):
    """Power BI RLS 對照表：Power BI 登入帳號 → 可看的學校。由 StaffProfile 產生。"""
    powerbi_upn = models.CharField(max_length=254, verbose_name='Power BI 登入帳號')
    university = models.CharField(max_length=200, verbose_name='學校')

    class Meta:
        db_table = 'insights_staff_access'
        verbose_name = '分析表：Power BI 權限對照'
        verbose_name_plural = '分析表：Power BI 權限對照'

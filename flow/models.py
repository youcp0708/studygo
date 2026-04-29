"""
flow/models.py
模塊二：個人化流程與任務管理
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta


CATEGORY_CHOICES = [
    ('visa',       '簽證辦理'),
    ('enrollment', '入學手續'),
    ('housing',    '住宿安排'),
    ('health',     '健保醫療'),
    ('finance',    '財務銀行'),
    ('language',   '語言學習'),
    ('culture',    '生活適應'),
    ('other',      '其他事項'),
]

CATEGORY_ICONS = {
    'visa':       '🛂',
    'enrollment': '🎓',
    'housing':    '🏠',
    'health':     '🏥',
    'finance':    '💳',
    'language':   '📚',
    'culture':    '🌏',
    'other':      '📌',
}


# ══════════════════════════════════════════
# FLOW STEP TEMPLATE
# 管理員預設的各類學生任務範本
# ══════════════════════════════════════════
class FlowStepTemplate(models.Model):
    title              = models.CharField(max_length=200, verbose_name='任務名稱')
    description        = models.TextField(blank=True, verbose_name='任務說明')
    category           = models.CharField(max_length=20, choices=CATEGORY_CHOICES,
                                          default='other', verbose_name='分類')
    identity_types     = models.JSONField(default=list, blank=True,
                                          verbose_name='適用身份別',
                                          help_text='空列表 = 所有身份別')
    admission_statuses = models.JSONField(default=list, blank=True,
                                          verbose_name='適用入學狀態',
                                          help_text='空列表 = 所有入學狀態')
    order              = models.PositiveSmallIntegerField(default=0, verbose_name='排序')
    is_required        = models.BooleanField(default=True, verbose_name='必要任務')
    days_offset        = models.IntegerField(
        null=True, blank=True, verbose_name='截止日偏移（天）',
        help_text='相對於預計抵台日期；負數=抵台前，正數=抵台後，空=無截止日'
    )
    reference_url      = models.URLField(blank=True, verbose_name='參考連結')
    is_active          = models.BooleanField(default=True, verbose_name='啟用')

    class Meta:
        ordering            = ['order']
        db_table            = 'flow_steptemplate'
        verbose_name        = '任務模板'
        verbose_name_plural = '任務模板'

    def __str__(self):
        return f'[{self.get_category_display()}] {self.title}'

    def applies_to(self, identity_type, admission_status):
        id_ok = not self.identity_types or identity_type in self.identity_types
        st_ok = not self.admission_statuses or admission_status in self.admission_statuses
        return id_ok and st_ok


# ══════════════════════════════════════════
# PROCESS FLOW
# 學生的個人化流程（由 StudentProfile 生成）
# ══════════════════════════════════════════
class ProcessFlow(models.Model):
    user             = models.OneToOneField(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='process_flow',
        verbose_name='使用者',
    )
    identity_type    = models.CharField(max_length=30, verbose_name='身份別（快照）')
    admission_status = models.CharField(max_length=20, verbose_name='入學狀態（快照）')
    created_at       = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at       = models.DateTimeField(auto_now=True,     verbose_name='更新時間')

    class Meta:
        db_table            = 'flow_processflow'
        verbose_name        = '個人化流程'
        verbose_name_plural = '個人化流程'

    def __str__(self):
        return f'{self.user.name} 的個人化流程'

    @property
    def completion_rate(self):
        total = self.tasks.count()
        if not total:
            return 0
        return round(self.tasks.filter(status='done').count() / total * 100)

    @property
    def done_count(self):
        return self.tasks.filter(status='done').count()

    @property
    def pending_count(self):
        return self.tasks.filter(status__in=['todo', 'in_progress']).count()

    @property
    def overdue_count(self):
        return self.tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=timezone.now().date(),
        ).count()


# ══════════════════════════════════════════
# USER TASK
# 學生的個別任務（由模板實例化）
# ══════════════════════════════════════════
class UserTask(models.Model):
    STATUS_CHOICES = [
        ('todo',        '待辦'),
        ('in_progress', '進行中'),
        ('done',        '已完成'),
    ]

    user         = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='使用者',
    )
    process_flow = models.ForeignKey(
        ProcessFlow,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='所屬流程',
    )
    template     = models.ForeignKey(
        FlowStepTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='來源模板',
    )
    title        = models.CharField(max_length=200, verbose_name='任務名稱')
    description  = models.TextField(blank=True, verbose_name='任務說明')
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES,
                                    default='other', verbose_name='分類')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                    default='todo', verbose_name='狀態')
    is_required  = models.BooleanField(default=True, verbose_name='必要任務')
    order        = models.PositiveSmallIntegerField(default=0, verbose_name='排序')
    due_date     = models.DateField(null=True, blank=True, verbose_name='截止日期')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成時間')
    notes        = models.TextField(blank=True, verbose_name='備註')
    created_at   = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at   = models.DateTimeField(auto_now=True,     verbose_name='更新時間')

    class Meta:
        ordering            = ['order', 'due_date']
        db_table            = 'flow_usertask'
        verbose_name        = '使用者任務'
        verbose_name_plural = '使用者任務'

    def __str__(self):
        return f'{self.user.name} — {self.title} [{self.get_status_display()}]'

    @property
    def is_overdue(self):
        return (
            self.due_date
            and self.status != 'done'
            and self.due_date < timezone.now().date()
        )

    def mark_done(self):
        self.status       = 'done'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

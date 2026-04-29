"""
flow/models.py
模塊二：流程模塊
"""

from django.db import models
from users.models import CustomUser


class FlowStep(models.Model):
    """流程步驟（系統預設，由管理員建立）"""

    CATEGORY_CHOICES = [
        ('pre_apply',   '申請前準備'),
        ('pre_arrival', '抵台前辦理'),
        ('post_arrival','抵台後辦理'),
        ('in_school',   '在學期間'),
    ]

    IDENTITY_CHOICES = [
        ('all',              '全部'),
        ('overseas_chinese', '僑生'),
        ('foreign_student',  '外籍生'),
        ('exchange',         '交換生'),
        ('preparatory',      '僑大先修生'),
    ]

    title         = models.CharField(max_length=200, verbose_name='步驟名稱')
    description   = models.TextField(verbose_name='說明', blank=True)
    category      = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='階段')
    identity_type = models.CharField(max_length=20, choices=IDENTITY_CHOICES,
                                     default='all', verbose_name='適用身份')
    order         = models.PositiveIntegerField(default=0, verbose_name='順序')
    deadline_days = models.IntegerField(null=True, blank=True, verbose_name='建議完成天數')
    is_active     = models.BooleanField(default=True, verbose_name='啟用')

    class Meta:
        db_table  = 'flow_step'
        ordering  = ['category', 'order']
        verbose_name = '流程步驟'
        verbose_name_plural = '流程步驟'

    def __str__(self):
        return f'[{self.get_category_display()}] {self.title}'


class UserProgress(models.Model):
    """使用者的流程進度"""

    user    = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                related_name='progress', verbose_name='使用者')
    step    = models.ForeignKey(FlowStep, on_delete=models.CASCADE,
                                related_name='user_progress', verbose_name='步驟')
    is_done = models.BooleanField(default=False, verbose_name='已完成')
    done_at = models.DateTimeField(null=True, blank=True, verbose_name='完成時間')
    note    = models.TextField(blank=True, verbose_name='備註')

    class Meta:
        db_table = 'flow_userprogress'
        unique_together = ('user', 'step')
        verbose_name = '使用者進度'
        verbose_name_plural = '使用者進度'

    def __str__(self):
        status = '✓' if self.is_done else '○'
        return f'{status} {self.user.name} — {self.step.title}'
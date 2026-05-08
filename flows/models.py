from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import StudentProfile


# 流程階段：申請來台、抵台、辦理入學報到
class FlowStage(models.Model):
    # 中文欄位：原本欄位保留，當作繁體中文
    name = models.CharField(max_length=100, verbose_name="流程階段名稱")
    description = models.TextField(blank=True, verbose_name="階段說明")

    # 多語言欄位：給 admin 手動填
    name_en = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱 English")
    name_my = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱 Burmese")
    name_id = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱 Indonesian")
    name_ms = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱 Malay")
    name_th = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱 Thai")
    name_ja = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱 Japanese")
    name_ko = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱 Korean")

    description_en = models.TextField(blank=True, verbose_name="階段說明 English")
    description_my = models.TextField(blank=True, verbose_name="階段說明 Burmese")
    description_id = models.TextField(blank=True, verbose_name="階段說明 Indonesian")
    description_ms = models.TextField(blank=True, verbose_name="階段說明 Malay")
    description_th = models.TextField(blank=True, verbose_name="階段說明 Thai")
    description_ja = models.TextField(blank=True, verbose_name="階段說明 Japanese")
    description_ko = models.TextField(blank=True, verbose_name="階段說明 Korean")

    order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        db_table = "flows_stage"
        ordering = ["order"]

    def __str__(self):
        return self.name

    def get_name_by_lang(self, lang_code):
        """
        依照目前語言取得流程階段名稱。
        如果該語言沒有填資料，就回傳中文 name。
        """
        lang_map = {
            "en": self.name_en,
            "my": self.name_my,
            "id": self.name_id,
            "ms": self.name_ms,
            "th": self.name_th,
            "ja": self.name_ja,
            "ko": self.name_ko,
        }
        return lang_map.get(lang_code, "") or self.name

    def get_description_by_lang(self, lang_code):
        """
        依照目前語言取得流程階段說明。
        如果該語言沒有填資料，就回傳中文 description。
        """
        lang_map = {
            "en": self.description_en,
            "my": self.description_my,
            "id": self.description_id,
            "ms": self.description_ms,
            "th": self.description_th,
            "ja": self.description_ja,
            "ko": self.description_ko,
        }
        return lang_map.get(lang_code, "") or self.description


# 任務模板：系統預設的流程任務
class Task(models.Model):
    stage = models.ForeignKey(
        FlowStage,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="所屬流程階段"
    )

    # 中文欄位：原本欄位保留，當作繁體中文
    title = models.CharField(max_length=200, verbose_name="任務名稱")
    description = models.TextField(blank=True, verbose_name="任務說明")

    # 多語言欄位：給 admin 手動填
    title_en = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 English")
    title_my = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Burmese")
    title_id = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Indonesian")
    title_ms = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Malay")
    title_th = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Thai")
    title_ja = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Japanese")
    title_ko = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Korean")

    description_en = models.TextField(blank=True, verbose_name="任務說明 English")
    description_my = models.TextField(blank=True, verbose_name="任務說明 Burmese")
    description_id = models.TextField(blank=True, verbose_name="任務說明 Indonesian")
    description_ms = models.TextField(blank=True, verbose_name="任務說明 Malay")
    description_th = models.TextField(blank=True, verbose_name="任務說明 Thai")
    description_ja = models.TextField(blank=True, verbose_name="任務說明 Japanese")
    description_ko = models.TextField(blank=True, verbose_name="任務說明 Korean")

    # 用來判斷這個任務適合哪種學生
    identity_type = models.CharField(
        max_length=30,
        choices=StudentProfile.IDENTITY_CHOICES,
        blank=True,
        verbose_name="適用身份類型"
    )
    nationality = models.CharField(
        max_length=50,
        choices=StudentProfile.NATIONALITY_CHOICES,
        blank=True,
        verbose_name="適用國籍"
    )
    admission_status = models.CharField(
        max_length=20,
        choices=StudentProfile.ADMISSION_STATUS_CHOICES,
        blank=True,
        verbose_name="適用入學狀態"
    )
    official_url = models.URLField(
        blank=True,
        verbose_name="官方資源連結"
    )
    is_required = models.BooleanField(default=True, verbose_name="是否必做")
    order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        db_table = "flows_task"
        ordering = ["stage__order", "order"]

    def __str__(self):
        return self.title

    def get_title_by_lang(self, lang_code):
        """
        依照目前語言取得任務名稱。
        如果該語言沒有填資料，就回傳中文 title。
        """
        lang_map = {
            "en": self.title_en,
            "my": self.title_my,
            "id": self.title_id,
            "ms": self.title_ms,
            "th": self.title_th,
            "ja": self.title_ja,
            "ko": self.title_ko,
        }
        return lang_map.get(lang_code, "") or self.title

    def get_description_by_lang(self, lang_code):
        """
        依照目前語言取得任務說明。
        如果該語言沒有填資料，就回傳中文 description。
        """
        lang_map = {
            "en": self.description_en,
            "my": self.description_my,
            "id": self.description_id,
            "ms": self.description_ms,
            "th": self.description_th,
            "ja": self.description_ja,
            "ko": self.description_ko,
        }
        return lang_map.get(lang_code, "") or self.description


# 學生自己的任務進度
class StudentTask(models.Model):
    STATUS_CHOICES = [
        ("not_started", _("未開始")),
        ("in_progress", _("進行中")),
        ("completed", _("已完成")),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="student_tasks",
        verbose_name="學生"
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="student_tasks",
        verbose_name="任務"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started",
        verbose_name="完成狀態"
    )
    note = models.TextField(blank=True, default='', verbose_name="備註")
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="預計完成日期"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="完成時間"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        db_table = "flows_student_task"
        unique_together = ("student", "task")

    def __str__(self):
        return f"{self.student.user.name} - {self.task.title} - {self.status}"


class Reminder(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name="學生"
    )
    student_task = models.ForeignKey(
        StudentTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reminders",
        verbose_name="關聯學生任務"
    )
    message = models.TextField(verbose_name="提醒內容")
    is_read = models.BooleanField(default=False, verbose_name="是否已讀")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        db_table = "flows_reminder"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reminder for {self.student.user.name} - {'Read' if self.is_read else 'Unread'}"


# ==========================================
# Signals: 當任務被更新時自動檢查並產生提醒
# ==========================================
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta


@receiver(post_save, sender=StudentTask)
def auto_create_reminder_on_task_update(sender, instance, **kwargs):
    if instance.status in ["not_started", "in_progress"] and instance.due_date:
        today = timezone.now().date()
        target_date = today + timedelta(days=3)

        if instance.due_date <= target_date:
            if instance.due_date < today:
                message = f"您的任務「{instance.task.title}」已經逾期（截止日：{instance.due_date}），請盡快完成！"
            elif instance.due_date == today:
                message = f"您的任務「{instance.task.title}」今天到期，請記得完成！"
            else:
                days_left = (instance.due_date - today).days
                message = f"您的任務「{instance.task.title}」還有 {days_left} 天到期（{instance.due_date}）。"

            exists = Reminder.objects.filter(
                student_task=instance,
                is_read=False
            ).exists()

            if not exists:
                Reminder.objects.create(
                    student=instance.student,
                    student_task=instance,
                    message=message
                )
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import StudentProfile


# 流程階段：例如 來台前、抵台後、入學報到
class FlowStage(models.Model):
    name = models.CharField(max_length=100, verbose_name="流程階段名稱")
    name_my = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱-緬文")

    description = models.TextField(blank=True, verbose_name="階段說明")
    description_my = models.TextField(blank=True, verbose_name="階段說明-緬文")

    order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        db_table = "flows_stage"
        ordering = ["order"]

    def __str__(self):
        return self.name


# 任務模板：系統預設有哪些任務
class Task(models.Model):
    stage = models.ForeignKey(
        FlowStage,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="所屬流程階段"
    )

    title = models.CharField(max_length=200, verbose_name="任務名稱")
    title_my = models.CharField(max_length=200, blank=True, verbose_name="任務名稱-緬文")

    description = models.TextField(blank=True, verbose_name="任務說明")
    description_my = models.TextField(blank=True, verbose_name="任務說明-緬文")

    # 用來判斷這個任務適合哪種學生
    identity_type = models.CharField(
        max_length=30,
        choices=StudentProfile.IDENTITY_CHOICES, # 選項限制
        blank=True,
        verbose_name="適用身份別"
    )

    nationality = models.CharField(
        max_length=50,
        choices=StudentProfile.NATIONALITY_CHOICES,  # 選項限制
        blank=True,
        verbose_name="適用國籍"
    )

    admission_status = models.CharField(
        max_length=20,
        choices=StudentProfile.ADMISSION_STATUS_CHOICES, # 選項限制
        blank=True,
        verbose_name="適用入學狀態"
    )

    official_url = models.URLField(
        blank=True,
        verbose_name="官方資料連結"
    )

    is_required = models.BooleanField(default=True, verbose_name="是否必做")
    order = models.PositiveIntegerField(default=0, verbose_name="排序")

    class Meta:
        db_table = "flows_task"
        ordering = ["stage__order", "order"]

    def __str__(self):
        return self.title


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



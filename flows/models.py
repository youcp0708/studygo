from django.db import models
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField
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
    name_vi = models.CharField(max_length=100, blank=True, verbose_name="流程階段名稱 Vietnamese")

    description_en = models.TextField(blank=True, verbose_name="階段說明 English")
    description_my = models.TextField(blank=True, verbose_name="階段說明 Burmese")
    description_id = models.TextField(blank=True, verbose_name="階段說明 Indonesian")
    description_ms = models.TextField(blank=True, verbose_name="階段說明 Malay")
    description_th = models.TextField(blank=True, verbose_name="階段說明 Thai")
    description_ja = models.TextField(blank=True, verbose_name="階段說明 Japanese")
    description_ko = models.TextField(blank=True, verbose_name="階段說明 Korean")
    description_vi = models.TextField(blank=True, verbose_name="階段說明 Vietnamese")

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
            "vi": self.name_vi,
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
            "vi": self.description_vi,
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
    task_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="任務代碼",
        help_text="用來判斷同一類任務，例如 prepare_passport、apply_visa。學生前端不會顯示。"
)
    description = models.TextField(blank=True, verbose_name="任務說明")

    # 多語言欄位：給 admin 手動填
    title_en = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 English")
    title_my = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Burmese")
    title_id = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Indonesian")
    title_ms = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Malay")
    title_th = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Thai")
    title_ja = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Japanese")
    title_ko = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Korean")
    title_vi = models.CharField(max_length=200, blank=True, verbose_name="任務名稱 Vietnamese")

    description_en = models.TextField(blank=True, verbose_name="任務說明 English")
    description_my = models.TextField(blank=True, verbose_name="任務說明 Burmese")
    description_id = models.TextField(blank=True, verbose_name="任務說明 Indonesian")
    description_ms = models.TextField(blank=True, verbose_name="任務說明 Malay")
    description_th = models.TextField(blank=True, verbose_name="任務說明 Thai")
    description_ja = models.TextField(blank=True, verbose_name="任務說明 Japanese")
    description_ko = models.TextField(blank=True, verbose_name="任務說明 Korean")
    description_vi = models.TextField(blank=True, verbose_name="任務說明 Vietnamese")

    # 用來判斷這個任務適合哪種學生
    region = MultiSelectField(
        choices=StudentProfile.REGION_CHOICES,
        blank=True,
        null=True,
        verbose_name="適用地區"
    )
    identity_type = MultiSelectField(
        choices=StudentProfile.IDENTITY_CHOICES,
        blank=True,
        null=True,
        verbose_name="適用身份類型"
    )
    nationality = MultiSelectField(
        choices=StudentProfile.NATIONALITY_CHOICES,
        blank=True,
        null=True,
        verbose_name="適用國籍"
    )
    university = models.CharField(
        max_length=200,
        choices=StudentProfile.UNIVERSITY_CHOICES,
        blank=True,
        verbose_name="適用學校"
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

    # ── 需要的文件（多語言）──
    required_documents    = models.TextField(blank=True, verbose_name="需要的文件")
    required_documents_en = models.TextField(blank=True, verbose_name="需要的文件 English")
    required_documents_my = models.TextField(blank=True, verbose_name="需要的文件 Burmese")
    required_documents_id = models.TextField(blank=True, verbose_name="需要的文件 Indonesian")
    required_documents_ms = models.TextField(blank=True, verbose_name="需要的文件 Malay")
    required_documents_th = models.TextField(blank=True, verbose_name="需要的文件 Thai")
    required_documents_ja = models.TextField(blank=True, verbose_name="需要的文件 Japanese")
    required_documents_ko = models.TextField(blank=True, verbose_name="需要的文件 Korean")
    required_documents_vi = models.TextField(blank=True, verbose_name="需要的文件 Vietnamese")
    # ── 辦理地點（多語言）──
    apply_location    = models.CharField(max_length=200, blank=True, verbose_name="辦理地點")
    apply_location_en = models.CharField(max_length=200, blank=True, verbose_name="辦理地點 English")
    apply_location_my = models.CharField(max_length=200, blank=True, verbose_name="辦理地點 Burmese")
    apply_location_id = models.CharField(max_length=200, blank=True, verbose_name="辦理地點 Indonesian")
    apply_location_ms = models.CharField(max_length=200, blank=True, verbose_name="辦理地點 Malay")
    apply_location_th = models.CharField(max_length=200, blank=True, verbose_name="辦理地點 Thai")
    apply_location_ja = models.CharField(max_length=200, blank=True, verbose_name="辦理地點 Japanese")
    apply_location_ko = models.CharField(max_length=200, blank=True, verbose_name="辦理地點 Korean")
    apply_location_vi = models.CharField(max_length=200, blank=True, verbose_name="辦理地點 Vietnamese")

    apply_address = models.CharField(max_length=200, blank=True, verbose_name="辦理地址")
    apply_map_url = models.URLField(
        blank=True,
        verbose_name="辦理地點地圖連結",
        help_text="Google Maps 或其他地圖連結"
    )

    # ── 期限設定 ──
    DEADLINE_TYPE_CHOICES = [
        ('none',         '無截止日期'),
        ('text_only',    '只顯示文字說明'),
        ('from_arrival', '依抵台日期自動計算'),
    ]
    deadline_type = models.CharField(
        max_length=20,
        choices=DEADLINE_TYPE_CHOICES,
        default='none',
        verbose_name="期限類型"
    )
    deadline_days = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="計算天數（僅限 from_arrival 使用）",
        help_text="抵台後幾天內必須完成"
    )
    # ── 辦理時程文字（多語言）──
    deadline_text    = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字")
    deadline_text_en = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字 English")
    deadline_text_my = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字 Burmese")
    deadline_text_id = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字 Indonesian")
    deadline_text_ms = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字 Malay")
    deadline_text_th = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字 Thai")
    deadline_text_ja = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字 Japanese")
    deadline_text_ko = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字 Korean")
    deadline_text_vi = models.CharField(max_length=300, blank=True, verbose_name="辦理時程文字 Vietnamese")

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
            "vi": self.title_vi,
        }
        return lang_map.get(lang_code, "") or self.title

    def get_localized(self, lang_code):
        """
        依語言代碼回傳本任務的所有需要本地化的文字欄位。
        若該語言沒有填就回联中文預設。
        """
        # Map lang_code to field suffix
        suffix_map = {
            'en': '_en', 'my': '_my', 'id': '_id',
            'ms': '_ms', 'th': '_th', 'ja': '_ja',
            'ko': '_ko', 'vi': '_vi',
        }
        s = suffix_map.get(lang_code)  # None if not supported (= Chinese default)

        if s is None:
            # No translation needed — return Chinese defaults directly
            return {
                'title':              self.title,
                'description':        self.description,
                'required_documents': self.required_documents,
                'apply_location':     self.apply_location,
                'apply_address':      self.apply_address,
                'apply_map_url':      self.apply_map_url,
                'official_url':       self.official_url,
                'deadline_text':      self.deadline_text,
            }

        # Return translated field, falling back to Chinese if the translated field is empty
        def pick(base_val, field_name):
            translated = getattr(self, field_name, '') or ''
            return translated if translated.strip() else (base_val or '')

        return {
            'title':              pick(self.title,              f'title{s}'),
            'description':        pick(self.description,        f'description{s}'),
            'required_documents': pick(self.required_documents, f'required_documents{s}'),
            'apply_location':     pick(self.apply_location,     f'apply_location{s}'),
            'apply_address':      self.apply_address,   # 地址不翻譯（台灣地址）
            'apply_map_url':      self.apply_map_url,
            'official_url':       self.official_url,
            'deadline_text':      pick(self.deadline_text,      f'deadline_text{s}'),
        }


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
    note = models.TextField(
        blank=True,
        verbose_name="任務備註"
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
    # 當任務被標記為已完成時，檢查是否跳過了某些前置任務
    if instance.status == "completed":
        t = instance.task
        curr_stage_order = t.stage.order
        curr_task_order = t.order

        # 找出本學生所有「未完成」、且「排序在此任務之前」的任務
        # 排序定義在 Task.Meta: ordering = ["stage__order", "order"]
        from django.db.models import Q
        skipped_tasks = StudentTask.objects.filter(
            student=instance.student
        ).exclude(
            status='completed'
        ).filter(
            Q(task__stage__order__lt=curr_stage_order) |
            Q(task__stage__order=curr_stage_order, task__order__lt=curr_task_order)
        ).select_related('task', 'task__stage')

        if skipped_tasks.exists():
            # 取得當前慣用語言 (支援 zh-hant, en, vi, id, ms, th, ja, ko, my)
            from django.utils.translation import get_language
            active_lang = get_language() or 'zh-hant'
            lang = (active_lang.split('-')[0] if '-' in active_lang else active_lang).lower()

            task_title = t.get_title_by_lang(lang)
            skipped_titles = [st.task.get_title_by_lang(lang) for st in skipped_tasks]

            if lang == 'en':
                skipped_str = ", ".join([f'"{title}"' for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" and {len(skipped_titles) - 3} other tasks"
                message = f'You have completed "{task_title}", but the prior task(s) {skipped_str} is/are not yet completed. It is recommended to complete them in order!'
            elif lang == 'vi':
                skipped_str = ", ".join([f'"{title}"' for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" và {len(skipped_titles) - 3} nhiệm vụ khác"
                message = f'Bạn đã hoàn thành "{task_title}", nhưng (các) nhiệm vụ trước đó {skipped_str} chưa được hoàn thành. Khuyên bạn nên hoàn thành chúng theo thứ tự!'
            elif lang == 'id':
                skipped_str = ", ".join([f'"{title}"' for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" dan {len(skipped_titles) - 3} tugas lainnya"
                message = f'Anda telah menyelesaikan "{task_title}", tetapi tugas sebelumnya {skipped_str} belum diselesaikan. Disarankan untuk menyelesaikannya secara berurutan!'
            elif lang == 'ms':
                skipped_str = ", ".join([f'"{title}"' for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" dan {len(skipped_titles) - 3} tugasan lain"
                message = f'Anda telah menyelesaikan "{task_title}", tetapi tugasan sebelumnya {skipped_str} belum selesai. Disyorkan untuk menyelesaikannya mengikut urutan!'
            elif lang == 'th':
                skipped_str = ", ".join([f'"{title}"' for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" และอีก {len(skipped_titles) - 3} งาน"
                message = f'คุณได้ทำ "{task_title}" เสร็จสิ้นแล้ว แต่งานก่อนหน้า {skipped_str} ยังไม่เสร็จสมบูรณ์ ขอแนะนำให้ทำตามลำดับ!'
            elif lang == 'ja':
                skipped_str = "、".join([f'「{title}」' for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" など計 {len(skipped_titles)} 件のタスク"
                message = f'「{task_title}」を完了しましたが、前置タスク{skipped_str}が未完了です。順序通りに完了することをお勧めします！'
            elif lang == 'ko':
                skipped_str = ", ".join([f'"{title}"' for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" 등 총 {len(skipped_titles)}개 작업"
                message = f'"{task_title}"을(를) 완료했으나, 이전 작업인 {skipped_str}이(가) 아직 완료되지 않았습니다. 순서대로 완료하는 것을 권장합니다!'
            elif lang == 'my':
                skipped_str = ", ".join([f'"{title}"' for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" နှင့် အခြား {len(skipped_titles) - 3} ခု"
                message = f'သင်သည် "{task_title}" ကို ပြီးမြောက်ပြီးဖြစ်သော်လည်း ယခင်လုပ်ဆောင်ရမည့် {skipped_str} မပြီးသေးပါ။ အစီအစဉ်အတိုင်း လုပ်ဆောင်ရန် အကြံပြုပါသည်!'
            else:  # Default zh-hant
                skipped_str = "、".join([f"「{title}」" for title in skipped_titles[:3]])
                if len(skipped_titles) > 3:
                    skipped_str += f" 等共 {len(skipped_titles)} 個任務"
                message = f"您已完成「{task_title}」，但前置任務 {skipped_str} 尚未完成，建議您依序完成！"

            # 檢查是否已經有未讀的相同提醒，避免重複發送
            exists = Reminder.objects.filter(
                student=instance.student,
                student_task=instance,
                is_read=False
            ).exists()

            if not exists:
                Reminder.objects.create(
                    student=instance.student,
                    student_task=instance,
                    message=message
                )


# ==========================================
# 小貼士（Tips）：後台可管理的實用資訊
# ==========================================
class Tip(models.Model):
    """
    小貼士：提供學生實用資訊，例如獎學金查詢、工作許可、護照遺失處理等。
    管理員可在 Django Admin 新增 / 編輯，前端會在流程頁面右側欄顯示。
    """
    # ── 中文（預設）──
    title = models.CharField(max_length=200, verbose_name="標題")
    content = models.TextField(blank=True, verbose_name="內容說明")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")
    order = models.PositiveIntegerField(default=0, verbose_name="排序")

    # ── 多語言：標題 ──
    title_en = models.CharField(max_length=200, blank=True, verbose_name="標題 English")
    title_my = models.CharField(max_length=200, blank=True, verbose_name="標題 Burmese")
    title_id = models.CharField(max_length=200, blank=True, verbose_name="標題 Indonesian")
    title_ms = models.CharField(max_length=200, blank=True, verbose_name="標題 Malay")
    title_th = models.CharField(max_length=200, blank=True, verbose_name="標題 Thai")
    title_ja = models.CharField(max_length=200, blank=True, verbose_name="標題 Japanese")
    title_ko = models.CharField(max_length=200, blank=True, verbose_name="標題 Korean")
    title_vi = models.CharField(max_length=200, blank=True, verbose_name="標題 Vietnamese")

    # ── 多語言：內容 ──
    content_en = models.TextField(blank=True, verbose_name="內容 English")
    content_my = models.TextField(blank=True, verbose_name="內容 Burmese")
    content_id = models.TextField(blank=True, verbose_name="內容 Indonesian")
    content_ms = models.TextField(blank=True, verbose_name="內容 Malay")
    content_th = models.TextField(blank=True, verbose_name="內容 Thai")
    content_ja = models.TextField(blank=True, verbose_name="內容 Japanese")
    content_ko = models.TextField(blank=True, verbose_name="內容 Korean")
    content_vi = models.TextField(blank=True, verbose_name="內容 Vietnamese")

    class Meta:
        db_table = "flows_tip"
        ordering = ["order"]
        verbose_name = "Tip"
        verbose_name_plural = "Tips"

    def __str__(self):
        return self.title

    def get_localized(self, lang_code):
        """
        依語言代碼回傳本地化的標題與內容。
        若該語言沒有填就回傳中文預設。
        """
        suffix_map = {
            'en': '_en', 'my': '_my', 'id': '_id',
            'ms': '_ms', 'th': '_th', 'ja': '_ja',
            'ko': '_ko', 'vi': '_vi',
        }
        s = suffix_map.get(lang_code)

        if s is None:
            return {
                'title': self.title,
                'content': self.content,
            }

        def pick(base_val, field_name):
            translated = getattr(self, field_name, '') or ''
            return translated if translated.strip() else (base_val or '')

        return {
            'title': pick(self.title, f'title{s}'),
            'content': pick(self.content, f'content{s}'),
        }

class TipLink(models.Model):
    """
    一筆小貼士的可重複鏈結。
    - `url`   : 真正的網址
    - `label` : 顯示在前端的文字（如「官方網站」/「申請表」），可留空，若空會直接顯示 URL 本身
    """
    tip = models.ForeignKey(
        Tip,
        on_delete=models.CASCADE,
        related_name="links",   # Tip.links -> QuerySet[TipLink]
        verbose_name="所屬小貼士"
    )
    url = models.URLField(verbose_name="鏈結網址")
    label = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="鏈結顯示文字",
        help_text="留空則直接使用 URL 作為顯示文字"
    )

    class Meta:
        db_table = "flows_tip_link"
        ordering = ["id"]
        verbose_name = "小貼士鏈結"
        verbose_name_plural = "小貼士鏈結"

    def __str__(self):
        return self.label or self.url

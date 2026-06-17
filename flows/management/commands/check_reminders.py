from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from flows.models import StudentTask, Reminder

class Command(BaseCommand):
    help = '自動掃描 StudentTask 的預計完成日期(due_date)，為即將到期或已過期的任務產生 Reminder，並發送中/英文 Email 提醒'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='提早幾天產生提醒（預設3天）',
        )

    def handle(self, *args, **options):
        days_ahead = options['days']
        today = timezone.now().date()
        target_date = today + timedelta(days=days_ahead)

        # 篩選未完成、且期限類型為 'from_arrival' 且必要日期欄位均有資料的學生的任務
        pending_tasks = StudentTask.objects.filter(
            status__in=['not_started', 'in_progress'],
            task__deadline_type='from_arrival',
            task__deadline_days__isnull=False,
            student__expected_arrival__isnull=False
        ).select_related('student__user', 'task')

        created_count = 0

        for st in pending_tasks:
            # 動態計算到期日：預計抵台日 + 任務截止天數
            due_date = st.student.expected_arrival + timedelta(days=st.task.deadline_days)

            # 僅處理即將到期或已逾期的任務
            if due_date > target_date:
                continue

            pref_lang = (st.student.preferred_language or 'zh-hant').lower()
            use_zh = pref_lang.startswith('zh')

            # 決定語言代碼以取得本地化的任務標題
            lang_code = 'zh-hant' if use_zh else 'en'
            task_title = st.task.get_title_by_lang(lang_code) or st.task.title

            # 根據語系動態生成提醒訊息與 Email 內容
            if use_zh:
                if due_date < today:
                    message = f'您的任務「{task_title}」已過期（期限：{due_date}），請盡速完成。'
                elif due_date == today:
                    message = f'您的任務「{task_title}」今天到期，請記得完成。'
                else:
                    days_left = (due_date - today).days
                    message = f'您的任務「{task_title}」將於 {days_left} 天後到期（{due_date}）。'
                
                email_subject = f'【StudyGo Taiwan 提醒】您的任務狀態提醒'
                email_body = (
                    f'{st.student.user.name} 您好，\n\n'
                    f'{message}\n\n'
                    f'請登入系統完成您的任務！\n\n'
                    f'StudyGo Taiwan 團隊'
                )
            else:
                if due_date < today:
                    message = f'Your task "{task_title}" is overdue (Deadline: {due_date}). Please complete it as soon as possible.'
                elif due_date == today:
                    message = f'Your task "{task_title}" is due today. Please remember to complete it.'
                else:
                    days_left = (due_date - today).days
                    message = f'Your task "{task_title}" will expire in {days_left} day(s) (Deadline: {due_date}).'
                
                email_subject = f'[StudyGo Taiwan] Task Reminder Notification'
                email_body = (
                    f'Hello {st.student.user.name},\n\n'
                    f'{message}\n\n'
                    f'Please log in to the system to complete your task!\n\n'
                    f'StudyGo Taiwan Team'
                )

            # 檢查是否已經有未讀的提醒，避免重複產生
            existing_reminder = Reminder.objects.filter(
                student_task=st,
                is_read=False
            ).exists()

            if not existing_reminder:
                Reminder.objects.create(
                    student=st.student,
                    student_task=st,
                    message=message
                )
                created_count += 1

                # 發送 Email 提醒
                email = st.student.user.email
                if email:
                    try:
                        send_mail(
                            subject=email_subject,
                            message=email_body,
                            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@studygo.tw',
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        self.stdout.write(self.style.SUCCESS(f'成功寄送 Email 提醒給 {email}。'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'寄送 Email 提醒給 {email} 失敗: {e}'))

        self.stdout.write(self.style.SUCCESS(f'成功檢查提醒，共新增 {created_count} 筆新提醒。'))



import re

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from flows.models import StudentTask, Reminder

# 到期提醒訊息中一定包含 YYYY-MM-DD 格式的截止日；
# 前置任務提醒（signal 產生）沒有日期，清理舊提醒時必須跳過，避免被誤刪
DATE_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}')

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

        # 篩選未完成、且符合期限條件的學生任務
        from django.db.models import Q
        pending_tasks = StudentTask.objects.filter(
            status__in=['not_started', 'in_progress']
        ).filter(
            Q(task__deadline_type='from_arrival', task__deadline_days__isnull=False, student__expected_arrival__isnull=False) |
            Q(task__deadline_type='absolute', task__deadline_date__isnull=False)
        ).select_related('student__user', 'task')

        created_count = 0

        for st in pending_tasks:
            # 依期限類型計算截止日
            if st.task.deadline_type == 'from_arrival':
                due_date = st.student.expected_arrival + timedelta(days=st.task.deadline_days)
            else:  # absolute
                due_date = st.task.deadline_date

            # 如果截止日期已變更，且有未讀的舊「到期提醒」（內容含日期但不是當前截止日期），
            # 將其刪除以防誤導；不含日期的提醒（如前置任務提醒）不動
            old_unread_reminders = Reminder.objects.filter(
                student_task=st,
                is_read=False
            )
            for r in old_unread_reminders:
                if DATE_PATTERN.search(r.message) and str(due_date) not in r.message:
                    r.delete()

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
                
                email_subject = f'【ReadyTo Taiwan 提醒】您的任務狀態提醒'
                email_body = (
                    f'{st.student.user.name} 您好，\n\n'
                    f'{message}\n\n'
                    f'請登入系統完成您的任務！\n\n'
                    f'ReadyTo Taiwan 團隊\n\n'
                    f'*本信件為系統自動發送，請勿回覆。'
                )
            else:
                if due_date < today:
                    message = f'Your task "{task_title}" is overdue (Deadline: {due_date}). Please complete it as soon as possible.'
                elif due_date == today:
                    message = f'Your task "{task_title}" is due today. Please remember to complete it.'
                else:
                    days_left = (due_date - today).days
                    message = f'Your task "{task_title}" will expire in {days_left} day(s) (Deadline: {due_date}).'
                
                email_subject = f'[ReadyTo Taiwan] Task Reminder Notification'
                email_body = (
                    f'Hello {st.student.user.name},\n\n'
                    f'{message}\n\n'
                    f'Please log in to the system to complete your task!\n\n'
                    f'ReadyTo Taiwan Team\n\n'
                    f'*This email was sent automatically by the system; please do not reply.'
                )

            # 檢查是否已經有針對此截止日期的提醒（不論已讀或未讀，避免對同一個截止日重複產生與發送）
            has_current_reminder = Reminder.objects.filter(
                student_task=st,
                message__contains=str(due_date)
            ).exists()

            if not has_current_reminder:
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



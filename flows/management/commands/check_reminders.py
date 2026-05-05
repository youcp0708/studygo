from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from flows.models import StudentTask, Reminder

class Command(BaseCommand):
    help = '自動掃描 StudentTask 的預計完成日期(due_date)，為即將到期或已過期的任務產生 Reminder'

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

        # 找出尚未完成且有 due_date 的任務
        pending_tasks = StudentTask.objects.filter(
            status__in=['not_started', 'in_progress'],
            due_date__isnull=False,
            due_date__lte=target_date
        )

        created_count = 0

        for st in pending_tasks:
            # 決定提醒的文字
            if st.due_date < today:
                message = f'您的任務「{st.task.title}」已過期（期限：{st.due_date}），請盡速完成。'
            elif st.due_date == today:
                message = f'您的任務「{st.task.title}」今天到期，請記得完成。'
            else:
                days_left = (st.due_date - today).days
                message = f'您的任務「{st.task.title}」將於 {days_left} 天後到期（{st.due_date}）。'

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

        self.stdout.write(self.style.SUCCESS(f'成功檢查提醒，共新增 {created_count} 筆新提醒。'))

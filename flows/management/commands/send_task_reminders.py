from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from flows.models import StudentTask
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Sends email reminders to students for tasks that are due soon or overdue.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        target_date = today + timedelta(days=3)

        # 找出狀態不是完成，且有設定 due_date 且即將到期或已逾期的任務
        tasks_to_remind = StudentTask.objects.filter(
            status__in=['not_started', 'in_progress'],
            due_date__lte=target_date,
            due_date__isnull=False
        ).select_related('student__user', 'task')

        reminders_sent = 0

        for student_task in tasks_to_remind:
            user = student_task.student.user
            if not user.email:
                continue

            task_title = student_task.task.title
            due_date = student_task.due_date

            if due_date < today:
                subject = f"【StudyGo Taiwan 提醒】任務已逾期：{task_title}"
                body = f"您好 {user.name}，\n\n您的任務「{task_title}」已經逾期（截止日：{due_date}）。\n請盡快登入系統完成任務！\n\nStudyGo Taiwan 團隊"
            elif due_date == today:
                subject = f"【StudyGo Taiwan 提醒】任務今日到期：{task_title}"
                body = f"您好 {user.name}，\n\n您的任務「{task_title}」將於今日（{due_date}）到期。\n請盡快登入系統完成任務！\n\nStudyGo Taiwan 團隊"
            else:
                days_left = (due_date - today).days
                subject = f"【StudyGo Taiwan 提醒】任務即將到期：{task_title}"
                body = f"您好 {user.name}，\n\n您的任務「{task_title}」還有 {days_left} 天到期（{due_date}）。\n請記得登入系統完成任務喔！\n\nStudyGo Taiwan 團隊"

            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@studygotaiwan.com',
                    [user.email],
                    fail_silently=False,
                )
                reminders_sent += 1
                self.stdout.write(self.style.SUCCESS(f"Sent email to {user.email} for task {task_title}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send email to {user.email}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Finished sending reminders. Total sent: {reminders_sent}"))

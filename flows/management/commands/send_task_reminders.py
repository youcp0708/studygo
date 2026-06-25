from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from flows.models import StudentTask, Reminder
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Sends email reminders to students for tasks that are due soon or overdue.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        target_date = today + timedelta(days=3)

        # 篩選未完成、且符合期限條件的學生任務
        from django.db.models import Q
        pending_tasks = StudentTask.objects.filter(
            status__in=['not_started', 'in_progress']
        ).filter(
            Q(task__deadline_type='from_arrival', task__deadline_days__isnull=False, student__expected_arrival__isnull=False) |
            Q(task__deadline_type='absolute', task__deadline_date__isnull=False)
        ).select_related('student__user', 'task')

        reminders_sent = 0

        for student_task in pending_tasks:
            # 依期限類型計算截止日
            if student_task.task.deadline_type == 'from_arrival':
                due_date = student_task.student.expected_arrival + timedelta(days=student_task.task.deadline_days)
            else:  # absolute
                due_date = student_task.task.deadline_date

            # 如果截止日期已變更，且有未讀的舊提醒（內容不含當前的截止日期），將其刪除以防誤導
            old_unread_reminders = Reminder.objects.filter(
                student_task=student_task,
                is_read=False
            )
            for r in old_unread_reminders:
                if str(due_date) not in r.message:
                    r.delete()

            # 僅處理即將到期或已逾期的任務
            if due_date > target_date:
                continue

            user = student_task.student.user
            if not user.email:
                continue

            pref_lang = (student_task.student.preferred_language or 'zh-hant').lower()
            use_zh = pref_lang.startswith('zh')

            # 決定語言代碼以取得本地化的任務標題
            lang_code = 'zh-hant' if use_zh else 'en'
            task_title = student_task.task.get_title_by_lang(lang_code) or student_task.task.title

            # 動態產生 message 內容 (用於資料庫記錄以進行重複檢查)
            if use_zh:
                if due_date < today:
                    message = f'您的任務「{task_title}」已過期（期限：{due_date}），請盡速完成。'
                    subject = f"【StudyGo Taiwan 提醒】任務已逾期：{task_title}"
                    body = f"您好 {user.name}，\n\n您的任務「{task_title}」已經逾期（截止日：{due_date}）。\n請盡快登入系統完成任務！\n\nStudyGo Taiwan 團隊"
                elif due_date == today:
                    message = f'您的任務「{task_title}」今天到期，請記得完成。'
                    subject = f"【StudyGo Taiwan 提醒】任務今日到期：{task_title}"
                    body = f"您好 {user.name}，\n\n您的任務「{task_title}」將於今日（{due_date}）到期。\n請盡快登入系統完成任務！\n\nStudyGo Taiwan 團隊"
                else:
                    days_left = (due_date - today).days
                    message = f'您的任務「{task_title}」將於 {days_left} 天後到期（{due_date}）。'
                    subject = f"【StudyGo Taiwan 提醒】任務即將到期：{task_title}"
                    body = f"您好 {user.name}，\n\n您的任務「{task_title}」還有 {days_left} 天到期（{due_date}）。\n請記得登入系統完成任務喔！\n\nStudyGo Taiwan 團隊"
            else:
                if due_date < today:
                    message = f'Your task "{task_title}" is overdue (Deadline: {due_date}). Please complete it as soon as possible.'
                    subject = f"[StudyGo Taiwan] Task Overdue: {task_title}"
                    body = f"Hello {user.name},\n\nYour task \"{task_title}\" is overdue (Deadline: {due_date}).\nPlease log in to the system and complete it as soon as possible!\n\nStudyGo Taiwan Team"
                elif due_date == today:
                    message = f'Your task "{task_title}" is due today. Please remember to complete it.'
                    subject = f"[StudyGo Taiwan] Task Due Today: {task_title}"
                    body = f"Hello {user.name},\n\nYour task \"{task_title}\" is due today ({due_date}).\nPlease log in to the system and complete it!\n\nStudyGo Taiwan Team"
                else:
                    days_left = (due_date - today).days
                    message = f'Your task "{task_title}" will expire in {days_left} day(s) (Deadline: {due_date}).'
                    subject = f"[StudyGo Taiwan] Task Expiring Soon: {task_title}"
                    body = f"Hello {user.name},\n\nYour task \"{task_title}\" will expire in {days_left} day(s) ({due_date}).\nPlease remember to log in to the system to complete it!\n\nStudyGo Taiwan Team"

            # 檢查是否已經有針對此截止日期的提醒（不論已讀或未讀，避免對同一個截止日重複產生與發送）
            has_current_reminder = Reminder.objects.filter(
                student_task=student_task,
                message__contains=str(due_date)
            ).exists()

            if not has_current_reminder:
                # 建立提醒記錄
                Reminder.objects.create(
                    student=student_task.student,
                    student_task=student_task,
                    message=message
                )

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


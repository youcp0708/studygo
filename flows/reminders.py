"""
掃描 StudentTask 的截止日期，為即將到期/今天到期/已過期的任務建立 Reminder。

被兩個地方呼叫：
- management command check_reminders：全站掃描 + 寄送 Email（排程用）
- flows.views.get_reminders_view：只掃描目前登入學生的任務，不寄 Email，
  讓使用者一打開通知鈴鐺就能即時看到已過期的提醒，不必依賴外部排程是否有跑。
"""
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

from .models import Reminder
from .reminder_messages import normalize_lang, render_due_message, render_due_email

# 到期提醒的三種 kind：due_soon（即將到期）、due_today（今天到期）、overdue（已過期）
DUE_KINDS = ('due_soon', 'due_today', 'overdue')


def sync_task_reminders(student_tasks, days_ahead=3, send_email=True, stdout=None):
    """
    為傳入的 StudentTask queryset 建立/清理到期提醒，並視需要補寄 Email。

    重點：提醒「是否已建立」跟「是否已寄過 Email」是分開追蹤的（見 Reminder.email_sent）。
    使用者自己開網站觸發的即時掃描（send_email=False）只會建立提醒、不寄信；
    之後排程以 send_email=True 執行時，即使提醒已經存在，只要 email_sent 還是 False，
    一樣會補寄，不會因為「提醒已存在」就永遠跳過寄信。

    :param student_tasks: StudentTask queryset（呼叫端負責篩選要掃描哪些學生/任務）
    :param days_ahead: 提早幾天產生「即將到期」提醒
    :param send_email: 是否同時寄送 Email 提醒
    :param stdout: 可選，用於輸出寄信結果（management command 用）
    :return: 新增的提醒數量
    """
    today = timezone.now().date()
    target_date = today + timedelta(days=days_ahead)

    pending_tasks = student_tasks.filter(
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

        # 如果截止日期已變更，刪除尚未讀取的舊「到期提醒」以防誤導；
        # 不含 kind 的提醒（如前置任務提醒）不受影響
        Reminder.objects.filter(
            student_task=st,
            is_read=False,
            kind__in=DUE_KINDS,
        ).exclude(due_date=due_date).delete()

        # 僅處理即將到期或已逾期的任務
        if due_date > target_date:
            continue

        if due_date < today:
            kind = 'overdue'
        elif due_date == today:
            kind = 'due_today'
        else:
            kind = 'due_soon'
        days_left = (due_date - today).days if kind == 'due_soon' else None

        pref_lang = normalize_lang(st.student.preferred_language)
        task_title = st.task.get_title_by_lang(pref_lang) or st.task.title

        # 根據學生的慣用語言動態生成提醒訊息與 Email 內容
        message = render_due_message(kind, pref_lang, task_title, due_date, days_left)
        email_subject, email_body = render_due_email(pref_lang, st.student.user.name, message)

        reminder = Reminder.objects.filter(student_task=st, kind=kind, due_date=due_date).first()

        if reminder is None:
            reminder = Reminder.objects.create(
                student=st.student,
                student_task=st,
                message=message,
                kind=kind,
                due_date=due_date,
            )
            created_count += 1

        if send_email and not reminder.email_sent:
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
                    reminder.email_sent = True
                    reminder.save(update_fields=['email_sent'])
                    if stdout:
                        stdout.write(f'成功寄送 Email 提醒給 {email}。')
                except Exception as e:
                    if stdout:
                        stdout.write(f'寄送 Email 提醒給 {email} 失敗: {e}')

    return created_count

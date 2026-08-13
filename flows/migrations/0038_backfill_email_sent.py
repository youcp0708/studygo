# 回填 email_sent：2026-08-12 06:18-06:19 那次 check_reminders 第一次成功執行時
# 實際寄出的 21 筆提醒（id 已由 reminders.py 的 send_mail 呼叫紀錄核對確認），標記為已寄過信，
# 避免下次排程執行時被誤判成「還沒寄過」而重複寄送。
# 其餘既有提醒（多半是使用者自己開網站時即時建立、從未寄過信）維持預設 False，
# 讓下次排程執行時能補寄，這正是這次修正的目的。
from django.db import migrations

CONFIRMED_SENT_IDS = [
    184, 185, 186, 187, 188, 189, 190, 191, 192, 193,
    194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204,
]


def mark_confirmed_as_sent(apps, schema_editor):
    Reminder = apps.get_model('flows', 'Reminder')
    Reminder.objects.filter(id__in=CONFIRMED_SENT_IDS).update(email_sent=True)


def reverse_noop(apps, schema_editor):
    Reminder = apps.get_model('flows', 'Reminder')
    Reminder.objects.filter(id__in=CONFIRMED_SENT_IDS).update(email_sent=False)


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0037_reminder_email_sent'),
    ]

    operations = [
        migrations.RunPython(mark_confirmed_as_sent, reverse_noop),
    ]

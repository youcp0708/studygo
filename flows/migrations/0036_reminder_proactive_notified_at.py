# Generated manually to match Django's migration format (mirrors 0035)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0035_reminder_due_date_reminder_kind_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='proactive_notified_at',
            field=models.DateTimeField(blank=True, help_text='非空代表這則提醒已經包裝成一則 helper 模式的主動 AI 訊息，避免重複生成', null=True, verbose_name='主動 AI 訊息已發送時間'),
        ),
    ]

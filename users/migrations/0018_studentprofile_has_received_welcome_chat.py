from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_studentprofile_has_seen_dashboard_tour'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='has_received_welcome_chat',
            field=models.BooleanField(default=False, verbose_name='是否已收到 AI 歡迎訊息'),
        ),
    ]

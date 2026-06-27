# Generated for ReadyToTaiwan chatbot module

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='新的對話', max_length=120, verbose_name='對話標題')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='建立時間')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新時間')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_sessions', to=settings.AUTH_USER_MODEL, verbose_name='使用者')),
            ],
            options={
                'verbose_name': '聊天對話',
                'verbose_name_plural': '聊天對話',
                'db_table': 'chatbot_chatsession',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', '使用者'), ('assistant', 'AI 小幫手'), ('system', '系統')], max_length=20, verbose_name='角色')),
                ('content', models.TextField(verbose_name='訊息內容')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='建立時間')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chatbot.chatsession', verbose_name='所屬對話')),
            ],
            options={
                'verbose_name': '聊天訊息',
                'verbose_name_plural': '聊天訊息',
                'db_table': 'chatbot_chatmessage',
                'ordering': ['created_at'],
            },
        ),
    ]

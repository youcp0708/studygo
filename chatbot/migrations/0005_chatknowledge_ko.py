# Generated manually for adding Korean fields to ChatKnowledge.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0004_chatknowledge'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatknowledge',
            name='title_ko',
            field=models.CharField(blank=True, max_length=200, verbose_name='韓文標題'),
        ),
        migrations.AddField(
            model_name='chatknowledge',
            name='content_ko',
            field=models.TextField(blank=True, verbose_name='韓文內容'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_school_schoolunit'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='has_seen_dashboard_tour',
            field=models.BooleanField(default=False, verbose_name='是否已看過 Dashboard 導覽'),
        ),
    ]

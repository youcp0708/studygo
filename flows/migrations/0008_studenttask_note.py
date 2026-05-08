from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0007_flowstage_description_en_flowstage_description_id_and_more'),
    ]

    operations = [
        # 欄位已存在於 DB，只需同步 Django state；
        # DB 端設定 default 並清掉現有的 NULL 值。
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='studenttask',
                    name='note',
                    field=models.TextField(blank=True, default='', verbose_name='備註'),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "UPDATE flows_student_task SET note = '' WHERE note IS NULL; "
                        "ALTER TABLE flows_student_task ALTER COLUMN note SET DEFAULT ''; "
                        "ALTER TABLE flows_student_task ALTER COLUMN note SET NOT NULL;"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]

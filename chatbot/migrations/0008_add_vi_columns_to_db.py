from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0007_merge_20260513_2036'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE chatbot_knowledge ADD COLUMN IF NOT EXISTS title_vi varchar(200);",
            reverse_sql="ALTER TABLE chatbot_knowledge DROP COLUMN IF EXISTS title_vi;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE chatbot_knowledge ADD COLUMN IF NOT EXISTS content_vi text;",
            reverse_sql="ALTER TABLE chatbot_knowledge DROP COLUMN IF EXISTS content_vi;",
        ),
    ]
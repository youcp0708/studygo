from django.db import migrations, connection

def add_vi_columns(apps, schema_editor):
    if 'sqlite' in connection.vendor:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(chatbot_knowledge)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'title_vi' not in columns:
            schema_editor.execute("ALTER TABLE chatbot_knowledge ADD COLUMN title_vi varchar(200);")
        if 'content_vi' not in columns:
            schema_editor.execute("ALTER TABLE chatbot_knowledge ADD COLUMN content_vi text;")
    else:
        schema_editor.execute("ALTER TABLE chatbot_knowledge ADD COLUMN IF NOT EXISTS title_vi varchar(200);")
        schema_editor.execute("ALTER TABLE chatbot_knowledge ADD COLUMN IF NOT EXISTS content_vi text;")

def reverse_add_vi_columns(apps, schema_editor):
    if 'sqlite' in connection.vendor:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(chatbot_knowledge)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'title_vi' in columns:
            # SQLite doesn't support dropping columns in some older versions,
            # but we can try or just skip in tests.
            try:
                schema_editor.execute("ALTER TABLE chatbot_knowledge DROP COLUMN title_vi;")
            except Exception:
                pass
        if 'content_vi' in columns:
            try:
                schema_editor.execute("ALTER TABLE chatbot_knowledge DROP COLUMN content_vi;")
            except Exception:
                pass
    else:
        schema_editor.execute("ALTER TABLE chatbot_knowledge DROP COLUMN IF EXISTS title_vi;")
        schema_editor.execute("ALTER TABLE chatbot_knowledge DROP COLUMN IF EXISTS content_vi;")


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0007_merge_20260513_2036'),
    ]

    operations = [
        migrations.RunPython(add_vi_columns, reverse_code=reverse_add_vi_columns),
    ]
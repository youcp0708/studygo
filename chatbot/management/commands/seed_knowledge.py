"""
chatbot/management/commands/seed_knowledge.py

把 chatbot/knowledge_data/ 底下的知識庫資料寫入 ChatKnowledge。

設計重點：
1. 資料以 Python 檔案版控，每筆都可 review、可重跑、可追來源。
2. 以 (category, university, country, identity_type, title) 為自然鍵做 upsert，
   重跑不會產生重複資料。
3. 只寫入繁體中文欄位與來源連結；各語系翻譯欄位不動，
   避免覆蓋掉管理員或翻譯流程已經填好的內容。

用法：
    python manage.py seed_knowledge              # 全部載入
    python manage.py seed_knowledge --only visa  # 只載入某個資料模組
    python manage.py seed_knowledge --dry-run    # 只列出會做什麼，不寫入
"""

from django.core.management.base import BaseCommand

from chatbot.knowledge_data import iter_modules


class Command(BaseCommand):
    help = '從 chatbot/knowledge_data/ 載入知識庫內容到 ChatKnowledge'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only', default='',
            help='只載入指定模組（檔名，不含 .py），例如：--only visa',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='只顯示會新增/更新哪些內容，不實際寫入資料庫',
        )

    def handle(self, *args, **options):
        from chatbot.models import ChatKnowledge

        only = options['only'].strip()
        dry_run = options['dry_run']
        verbosity = options['verbosity']

        created = updated = unchanged = 0

        for module_name, entries in iter_modules(only=only):
            for entry in entries:
                natural_key = {
                    'category':      entry['category'],
                    'university':    entry.get('university', ''),
                    'country':       entry.get('country', ''),
                    'identity_type': entry.get('identity_type', ''),
                    'title':         entry['title'],
                }
                payload = {
                    'keywords':   entry.get('keywords', ''),
                    'content':    entry['content'].strip(),
                    'source_url': entry.get('source_url', ''),
                    'bot_type':   entry.get('bot_type', 'helper'),
                    'discipline': entry.get('discipline', ''),
                    'is_active':  True,
                }
                # 只有資料檔明確標註查核日期時才寫入，否則保持「未查核」
                if entry.get('verified_at'):
                    payload['last_verified_at'] = entry['verified_at']

                if dry_run:
                    exists = ChatKnowledge.objects.filter(**natural_key).exists()
                    if verbosity:
                        action = '更新' if exists else '新增'
                        self.stdout.write(f'[{module_name}] {action}：{entry["title"]}')
                    if exists:
                        updated += 1
                    else:
                        created += 1
                    continue

                obj, was_created = ChatKnowledge.objects.get_or_create(
                    **natural_key, defaults=payload
                )
                if was_created:
                    created += 1
                    continue

                changed = [f for f, v in payload.items() if getattr(obj, f) != v]
                if changed:
                    for field in changed:
                        setattr(obj, field, payload[field])
                    obj.save(update_fields=changed)
                    updated += 1
                else:
                    unchanged += 1

        if verbosity:
            prefix = '[dry-run] ' if dry_run else ''
            self.stdout.write(self.style.SUCCESS(
                f'{prefix}新增 {created} 筆、更新 {updated} 筆、未變動 {unchanged} 筆。'
            ))

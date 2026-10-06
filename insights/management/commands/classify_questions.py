"""
python manage.py classify_questions [--limit 2000] [--no-llm]

把學生向 AI 小幫手（helper 模式）的提問分類。先跑這個，再跑 build_insights。
"""

from django.core.management.base import BaseCommand

from insights.classify import classify_pending


class Command(BaseCommand):
    help = 'Student Insights：分類學生的 AI 提問（只處理尚未分類的訊息）'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=2000, help='本次最多處理幾則訊息')
        parser.add_argument('--no-llm', action='store_true', help='只用關鍵字規則，不呼叫 OpenAI')

    def handle(self, *args, **options):
        stats = classify_pending(limit=options['limit'], use_llm=not options['no_llm'])
        self.stdout.write(self.style.SUCCESS(
            f'分類完成：規則 {stats["rule"]} 則、LLM {stats["llm"]} 則、歸為其他 {stats["none"]} 則'
        ))
        if stats['llm_failed']:
            self.stdout.write(self.style.WARNING(
                f'{stats["llm_failed"]} 則 LLM 呼叫失敗，下次執行會再試'
            ))

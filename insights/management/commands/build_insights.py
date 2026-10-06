"""
python manage.py build_insights [--date YYYY-MM-DD]

重建 Student Insights 分析表（insights_*）。建議每日排程執行一次，
並在 Microsoft Fabric Data Factory 複製資料之前完成。
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from insights.build import build_snapshot


class Command(BaseCommand):
    help = 'Student Insights：重建去識別化分析表與風險預警'

    def add_arguments(self, parser):
        parser.add_argument('--date', help='資料日期（預設今天），格式 YYYY-MM-DD')

    def handle(self, *args, **options):
        snapshot_date = None
        if options['date']:
            try:
                snapshot_date = date.fromisoformat(options['date'])
            except ValueError:
                raise CommandError('--date 格式應為 YYYY-MM-DD')

        summary = build_snapshot(snapshot_date)
        self.stdout.write(self.style.SUCCESS(
            f'分析表已重建（資料日期 {summary["snapshot_date"]}）：'
            f'學生 {summary["students"]}、學生任務 {summary["student_tasks"]}、'
            f'提問 {summary["questions"]}、預警 {summary["alerts"]}'
        ))

        unmapped = summary['unmapped_tasks']
        if unmapped:
            self.stdout.write(self.style.WARNING(
                f'\n有 {len(unmapped)} 個任務被歸類為「其他」，'
                '請把它們的 task_code 補進 insights/task_categories.py 的 TASK_CODE_MAP：'
            ))
            for t in unmapped:
                self.stdout.write(
                    f'  Task #{t["task_id"]}  task_code="{t["task_code"]}"  {t["title"]}（{t["rows"]} 筆）'
                )

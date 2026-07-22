from django.core.management.base import BaseCommand

from flows.models import StudentTask
from flows.reminders import sync_task_reminders


class Command(BaseCommand):
    help = '自動掃描 StudentTask 的預計完成日期(due_date)，為即將到期或已過期的任務產生 Reminder，並發送中/英文 Email 提醒'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='提早幾天產生提醒（預設3天）',
        )

    def handle(self, *args, **options):
        days_ahead = options['days']

        created_count = sync_task_reminders(
            StudentTask.objects.all(),
            days_ahead=days_ahead,
            send_email=True,
            stdout=self.stdout,
        )

        self.stdout.write(self.style.SUCCESS(f'成功檢查提醒，共新增 {created_count} 筆新提醒。'))

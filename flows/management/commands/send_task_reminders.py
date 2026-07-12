from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    [已棄用] 此指令與 check_reminders 功能重複，且原本沒有去重機制，
    排成每日 cron 會對同一個到期任務重複寄信。

    為避免破壞既有排程，保留此指令名稱，但內部直接轉呼叫 check_reminders
    （check_reminders 會以「同一截止日只提醒一次」去重，並同時建立站內提醒與寄送 Email）。
    """

    help = '[Deprecated] 請改用 check_reminders。此指令會直接轉呼叫 check_reminders。'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='提早幾天產生提醒（預設3天）',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'send_task_reminders 已棄用，改為執行 check_reminders（含去重與站內提醒）。'
        ))
        call_command('check_reminders', days=options['days'])

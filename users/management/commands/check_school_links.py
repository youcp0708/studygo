"""
users/management/commands/check_school_links.py

檢查各校連結是否還連得通，把結果寫回 SchoolLink.is_reachable / last_checked_at。

為什麼需要這支指令：
連結網址本身通常長年不變，但學校改版網站時會整批換路徑，舊連結就變成 404。
這是這份連結資料唯一會「默默壞掉」的方式 —— 頁面內容更新不會讓資料變錯
（因為我們只存網址、不存內容），但連結失效會讓學生點進去看到錯誤頁。

連結失效時不會自動刪除，只標記 is_reachable=False，
chatbot 會據此提醒學生改由學校首頁進入，後台也會顯示出來供人工修正。

用法：
    python manage.py check_school_links
    python manage.py check_school_links --school NCU
"""

from datetime import date

from django.core.management.base import BaseCommand

from users.models import School, SchoolLink


class Command(BaseCommand):
    help = '檢查 SchoolLink 的連結是否仍可連通，並更新檢查結果'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school', default='',
            help='只檢查指定學校代碼，例如：--school NCU',
        )
        parser.add_argument(
            '--timeout', type=int, default=10,
            help='單一連結的逾時秒數（預設 10）',
        )

    def handle(self, *args, **options):
        from studygo.http_compat import gov_edu_session

        # 這支指令只確認網址通不通，不送帳密也不採信回應內容，
        # 因此可以放寬到連得上只支援舊式 TLS 重新協商的校園伺服器（例如政大 iNCCU）
        session = gov_edu_session(allow_legacy_renegotiation=True)
        school_code = options['school'].strip()
        timeout = options['timeout']
        verbosity = options['verbosity']

        links = SchoolLink.objects.filter(is_active=True).select_related('school')
        if school_code:
            links = links.filter(school__code=school_code)

        links = list(links)
        today = date.today()

        # 先全部量測完再寫入，中間不動資料庫，這樣才有機會在寫入前做整體合理性判斷
        results = [(link, self._is_reachable(session, link.url, timeout)) for link in links]
        failed = [link for link, ok in results if not ok]

        # 熔斷：本機網路不穩（DNS 掛掉、離線、被防火牆擋）時會讓大量連結同時「連不通」。
        # 這種情況把整批標記成失效，chatbot 就會對學生說一堆正常連結壞了，比不檢查更糟。
        # 失敗率過半時判定問題在自己這端，直接放棄本次結果、不寫入任何東西。
        if links and len(failed) > len(links) / 2:
            if verbosity:
                self.stdout.write(self.style.ERROR(
                    f'中止：{len(links)} 筆中有 {len(failed)} 筆連不通（超過半數），'
                    '研判是本機網路問題而非學校網站失效，本次結果不寫入資料庫。'
                ))
                self.stdout.write('請確認網路連線後重跑。')
            return

        for link, ok in results:
            link.is_reachable = ok
            link.last_checked_at = today
            link.save(update_fields=['is_reachable', 'last_checked_at'])
            if not ok and verbosity:
                self.stdout.write(self.style.WARNING(
                    f'連不通：{link.school.code} {link.name} -> {link.url}'
                ))

        if verbosity:
            self.stdout.write(self.style.SUCCESS(
                f'完成：可連通 {len(links) - len(failed)} 筆、連不通 {len(failed)} 筆。'
            ))
            if failed:
                self.stdout.write(
                    '連不通的連結已標記 is_reachable=False，請到後台「學校線上系統連結」'
                    '確認學校是否改版並更新網址。資料不會自動刪除。'
                )

    def _is_reachable(self, session, url, timeout):
        """
        一律用 GET + stream=True：只取回應標頭就關閉連線，不下載內容。

        不用 HEAD 的原因：實測不少校園系統（例如 NTU COOL）對 HEAD 回 404、
        對 GET 卻回 200，用 HEAD 判斷會把正常的連結誤判成失效。
        誤判成失效會讓 chatbot 對學生說「這個連結可能壞了」，比不檢查更糟。

        取得 HTTP 狀態碼就直接判定，不重試（那是學校網站給的明確答案）；
        連線層失敗（逾時、DNS、TLS）才重試一次，因為那有可能只是網路抖動。
        """
        for attempt in range(2):
            try:
                resp = session.get(
                    url, timeout=timeout, allow_redirects=True, stream=True,
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; ReadyToTaiwan-LinkCheck/1.0)'},
                )
                try:
                    return resp.status_code < 400
                finally:
                    resp.close()
            except Exception:
                if attempt == 0:
                    continue
                return False
        return False

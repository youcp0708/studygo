"""
studygo/http_compat.py

連線臺灣政府機關與大學網站時的 HTTPS 相容處理。

問題背景：
不少 .gov.tw / .edu.tw 網站的憑證缺少 Subject Key Identifier 等擴充欄位。
瀏覽器與 curl 都能正常連線（代表憑證鏈本身可信），但 Python 3.13 預設啟用
VERIFY_X509_STRICT，會直接拒絕連線。

這裡只關閉 VERIFY_X509_STRICT 這一項檢查，其餘憑證鏈驗證、主機名稱比對
全部維持正常，跟 verify=False（完全不驗證憑證）是兩回事，
不應該被當成一般的「忽略憑證錯誤」寫法拿去別處重用。
"""

import ssl

import requests
from requests.adapters import HTTPAdapter


class RelaxedStrictFlagAdapter(HTTPAdapter):
    """
    只關閉 VERIFY_X509_STRICT，其餘 TLS 驗證照常。

    allow_legacy_renegotiation：另外允許 RFC 5746 之前的舊式重新協商。
    部分校園系統（例如政大 iNCCU）的伺服器只支援舊式協商，OpenSSL 3.x 預設會拒絕。
    這一項會讓連線理論上可能受到 2009 年的 renegotiation 前綴注入攻擊，
    因此只在「單純確認網址還通不通、不傳送任何帳密、也不信任回應內容」的場景才開啟，
    抓取資料並據以回答學生的情境一律不要開。
    """

    def __init__(self, *args, allow_legacy_renegotiation=False, **kwargs):
        self._allow_legacy_renegotiation = allow_legacy_renegotiation
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        if hasattr(ssl, 'VERIFY_X509_STRICT'):
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        if self._allow_legacy_renegotiation and hasattr(ssl, 'OP_LEGACY_SERVER_CONNECT'):
            ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def gov_edu_session(allow_legacy_renegotiation=False):
    """建立可連線政府 / 校園網站的 requests session。"""
    session = requests.Session()
    session.mount(
        'https://',
        RelaxedStrictFlagAdapter(allow_legacy_renegotiation=allow_legacy_renegotiation),
    )
    return session

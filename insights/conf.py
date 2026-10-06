"""
insights/conf.py
Student Insights 的設定值。全部從環境變數讀取，不需要改 studygo/settings.py。
"""

import os

from django.conf import settings

# 分組人數小於此值時不顯示數字（避免小樣本誤導、反推個人）
MIN_DISPLAY_N = 10

# 風險預警：分母至少要有這麼多筆才觸發
ALERT_MIN_N = 30
# 風險預警：與比較基準相差至少幾個百分點
ALERT_MIN_DELTA_PP = 3.0
# 風險預警：相對變化至少多少（0.3 = 30%）
ALERT_MIN_RELATIVE = 0.3

# 逾期未完成、且這麼多天沒登入 → 標示為「可能未回報」
UNREPORTED_INACTIVE_DAYS = 30


def use_demo_data():
    """INSIGHTS_USE_DEMO_DATA=True 時，Dashboard 讀取 seed_insights_demo 產生的模擬資料。"""
    return os.getenv('INSIGHTS_USE_DEMO_DATA', 'False') == 'True'


def hash_key():
    """
    產生 student_key 用的 HMAC 密鑰。
    建議在 .env 設定獨立的 INSIGHTS_HASH_KEY；未設定時退回 SECRET_KEY。
    """
    return (os.getenv('INSIGHTS_HASH_KEY') or settings.SECRET_KEY).encode('utf-8')


def excluded_email_domains():
    """
    不計入統計的 Email 網域（測試帳號），以逗號分隔，例如：
    INSIGHTS_EXCLUDED_EMAIL_DOMAINS=example.com,test.com
    """
    raw = os.getenv('INSIGHTS_EXCLUDED_EMAIL_DOMAINS', '')
    return [d.strip().lower().lstrip('@') for d in raw.split(',') if d.strip()]


def excluded_emails():
    """不計入統計的個別 Email（測試帳號），以逗號分隔。"""
    raw = os.getenv('INSIGHTS_EXCLUDED_EMAILS', '')
    return [e.strip().lower() for e in raw.split(',') if e.strip()]

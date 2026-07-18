"""
studygo/settings.py
Django 專案主設定檔
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

SECRET_KEY = 'django-insecure-請替換成隨機字串-production-key-here'

DEBUG = os.getenv('DEBUG', 'True') == 'True'  # 上線時在 .env 設 DEBUG=False

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '*').split(',') if h.strip()]

# ── 應用程式 ──
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',           # pip install djangorestframework
    'rest_framework.authtoken',
    'corsheaders',              # pip install django-cors-headers
    'users',                    # 使用者管理模塊（模塊一）
    'flows',                    # 流程模塊(模塊二)
    'guides',                   # 資訊中心指南
    'chatbot',                  # AI 聊天機器人
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'studygo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 全域 templates 目錄
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'studygo.wsgi.application'

# ── 資料庫 ──
DATABASES = {
    'default': {
        'ENGINE':   os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME':     os.getenv('DB_NAME', 'postgres'),
        'USER':     os.getenv('DB_USER', 'postgres.hpszxboxqzmvisydcnhz'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'uq6pUJAfP8wGIlCZ'),
        'HOST':     os.getenv('DB_HOST', 'aws-1-ap-southeast-1.pooler.supabase.com'),  # 你的 Supabase host
        'PORT':     os.getenv('DB_PORT', '5432'),
    }
}

import sys
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


# ── 密碼驗證 ──
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── 語言與時區 ──
LANGUAGE_CODE = 'zh-hant'
TIME_ZONE     = 'Asia/Taipei'
USE_I18N      = True
USE_TZ        = True

LANGUAGES = [
    ('zh-hant', '繁體中文'),
    ('en', 'English'),
    ('vi', 'Tiếng Việt'),
    ('my', 'မြန်မာဘာသာ'),
    ('id', 'Bahasa Indonesia'),
    ('ms', 'Bahasa Melayu'),
    ('th', 'ไทย'),
    ('ja', '日本語'),
    ('ko', '한국어'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ── 靜態檔案 ──
STATIC_URL  = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic 輸出

# ── 媒體檔案（如上傳頭像）──
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── 使用自訂 User Model ──
AUTH_USER_MODEL = 'users.CustomUser'

# ── Django REST Framework ──
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '300/day',
        'user': '1000/day',
        'login': '10/minute',           # 每分鐘最多 10 次登入嘗試
        'register': '20/hour',          # 每小時最多 20 次註冊
        'password_reset': '5/hour',     # 每小時最多 5 次重設密碼請求
        'resend_verification': '5/hour', # 每小時最多 5 次重發驗證信
    },
}

# ── CORS（前後端分離時使用）──
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:8000',
]
CORS_ALLOW_CREDENTIALS = True

# ── Email 設定 ──
# 使用環境變數設定 SMTP（Gmail 範例）：
#   $env:EMAIL_HOST_USER="your@gmail.com"
#   $env:EMAIL_HOST_PASSWORD="your_app_password"   ← Gmail 應用程式密碼（非帳號密碼）
# 若未設定 EMAIL_HOST_USER，自動退回 console 模式（印到終端機）
#
# 強制使用 console 模式，不發送真實信件給使用者（若要正式發信請改為 False）
FORCE_CONSOLE_EMAIL = True

_email_user = os.environ.get('EMAIL_HOST_USER', '')
if _email_user and not FORCE_CONSOLE_EMAIL:
    EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS       = True
    EMAIL_HOST_USER     = _email_user
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', _email_user)
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@readytotaiwan.tw'

# ── Email 驗證開關 ──
# demo / 開發環境設 False：註冊後不強制驗證信箱即可登入與填寫資料
# （console email 模式下真實使用者收不到驗證信，強制驗證會卡住整個流程）
REQUIRE_EMAIL_VERIFICATION = os.getenv('REQUIRE_EMAIL_VERIFICATION', 'False') == 'True'

# ── Google OAuth ──
# 在 Google Cloud Console 建立 OAuth 2.0 用戶端 ID 後填入：
#   $env:GOOGLE_CLIENT_ID="xxxx.apps.googleusercontent.com"
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

# ── Session 設定 ──
SESSION_COOKIE_AGE     = 60 * 60 * 24 * 7  # 7 天
SESSION_COOKIE_SECURE  = False  # 上線改 True（HTTPS）
SESSION_COOKIE_HTTPONLY= True

# ── CSRF ──
CSRF_COOKIE_SAMESITE = 'Lax'

# ── IP 來源設定 ──
# 只有確認部署在可信任的 Reverse Proxy（如 Nginx）後面時才設為 True
# 設為 False 時一律使用 REMOTE_ADDR，避免 X-Forwarded-For 被偽造
TRUST_X_FORWARDED_FOR = os.environ.get('TRUST_X_FORWARDED_FOR', 'False') == 'True'

# ── Google Sign-In 彈窗修復 ──
# Django 5.x 預設 COOP: same-origin 會阻擋 GSI popup 回傳 credential
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin-allow-popups'

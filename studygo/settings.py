"""
studygo/settings.py
Django 專案主設定檔
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(key, default=None, required=False):
    v = os.environ.get(key, default)
    if required and not v:
        raise ImproperlyConfigured(f"缺少必要環境變數：{key}")
    return v


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
# 中央氣象署開放資料平臺 Authorization key，免費申請：https://opendata.cwa.gov.tw/
CWA_API_KEY = os.getenv("CWA_API_KEY", "")

SECRET_KEY = env('SECRET_KEY', required=True)

DEBUG = os.getenv('DEBUG', 'False') == 'True'  # production 不設此變數即為 False

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# 正式網域（信件連結等場合使用，不信任 request.get_host()，避免 Host Header 攻擊）
SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'http://localhost:8000').rstrip('/')

# 上線後填入正式網域，例如 CSRF_TRUSTED_ORIGINS=https://readytotaiwan.tw,https://www.readytotaiwan.tw
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

# Render 會自動注入這個變數（如 your-app.onrender.com），自動放行避免忘記手動加入 ALLOWED_HOSTS
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

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
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
        'ENGINE':   env('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME':     env('DB_NAME', required=True),
        'USER':     env('DB_USER', required=True),
        'PASSWORD': env('DB_PASSWORD', required=True),
        'HOST':     env('DB_HOST', required=True),
        'PORT':     env('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {'sslmode': 'require'},
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

# ── 靜態檔案（無 Nginx，由 whitenoise 服務）──
STATIC_URL  = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic 輸出
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# ── 媒體檔案（如上傳頭像、chatbot 附件）──
# 本機開發預設用本機檔案系統；設定 SUPABASE_S3_ENDPOINT_URL 等環境變數後，
# 自動改用 Supabase Storage（S3-compatible），Render 上重新部署不會遺失檔案。
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

SUPABASE_S3_ENDPOINT_URL = os.environ.get('SUPABASE_S3_ENDPOINT_URL')
if SUPABASE_S3_ENDPOINT_URL:
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'endpoint_url': SUPABASE_S3_ENDPOINT_URL,
            'access_key': env('SUPABASE_S3_ACCESS_KEY_ID', required=True),
            'secret_key': env('SUPABASE_S3_SECRET_ACCESS_KEY', required=True),
            'bucket_name': env('SUPABASE_S3_BUCKET_NAME', required=True),
            'region_name': os.environ.get('SUPABASE_S3_REGION', 'ap-southeast-1'),
            'querystring_auth': False,
            'file_overwrite': False,
            'default_acl': None,
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── 使用自訂 User Model ──
AUTH_USER_MODEL = 'users.CustomUser'

# ── Django REST Framework ──
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
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
# 上線後改用實際前端網域，例如 CORS_ALLOWED_ORIGINS=https://readytotaiwan.tw
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:8000'
).split(',') if o.strip()]
CORS_ALLOW_CREDENTIALS = True

# ── 上傳大小上限 ──
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# ── Email 設定 ──
# 使用環境變數設定 SMTP（Gmail 範例）：
#   $env:EMAIL_HOST_USER="your@gmail.com"
#   $env:EMAIL_HOST_PASSWORD="your_app_password"   ← Gmail 應用程式密碼（非帳號密碼）
# 若未設定 EMAIL_HOST_USER，自動退回 console 模式（印到終端機）
#
# 強制使用 console 模式，不發送真實信件給使用者（若要正式發信請改為 False）
FORCE_CONSOLE_EMAIL = False

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
SESSION_COOKIE_HTTPONLY= True

# ── CSRF ──
CSRF_COOKIE_SAMESITE = 'Lax'

# ── IP 來源設定 ──
# 只有確認部署在可信任的 Reverse Proxy（如 Nginx）後面時才設為 True
# 設為 False 時一律使用 REMOTE_ADDR，避免 X-Forwarded-For 被偽造
TRUST_X_FORWARDED_FOR = os.environ.get('TRUST_X_FORWARDED_FOR', 'False') == 'True'

# ── HTTPS 強制 + 安全 Cookie（僅 production，即 DEBUG=False 時啟用） ──
# 本機開發用 http，維持 DEBUG=True 即可略過這些設定
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE    = not DEBUG

if not DEBUG:
    SECURE_SSL_REDIRECT   = True
    SECURE_HSTS_SECONDS   = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD   = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    if TRUST_X_FORWARDED_FOR:
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Google Sign-In 彈窗修復 ──
# Django 5.x 預設 COOP: same-origin 會阻擋 GSI popup 回傳 credential
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin-allow-popups'

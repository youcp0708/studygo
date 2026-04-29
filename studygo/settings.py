"""
studygo/settings.py
Django 專案主設定檔
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = 'django-insecure-請替換成隨機字串-production-key-here'

DEBUG = True  # 上線前改為 False

ALLOWED_HOSTS = ['*']  # 上線前改為實際網域

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
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',   # 必須在 CommonMiddleware 之前
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

# ── 資料庫（開發用 SQLite，上線換 PostgreSQL）──
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     'postgres',
        'USER':     'postgres',
        'PASSWORD': '112403046',
        'HOST':     'localhost',  # 你的 Supabase host
        'PORT':     '5432',
    }
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
_email_user = os.environ.get('EMAIL_HOST_USER', '')
if _email_user:
    EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS       = True
    EMAIL_HOST_USER     = _email_user
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', _email_user)
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@studygo.tw'

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

# ── Google Sign-In 彈窗修復 ──
# Django 5.x 預設 COOP: same-origin 會阻擋 GSI popup 回傳 credential
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin-allow-popups'

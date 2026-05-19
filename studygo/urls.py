"""
studygo/urls.py
專案根 URL 設定
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 使用者管理模塊（模塊一）
    # 前端頁面路由：/users/
    # API 路由：    # === App 路由 ===
    path('', include('users.urls')),                # Users app 前端
    path('api/', include('users.api_urls')),        # Users app API

    path('flows/', include('flows.urls')),          # Flows app 前端
    path('', include('guides.urls')),              # 資訊中心指南
    path('api/', include('flows.api_urls')),        # Flows app API

    path('chatbot/', include('chatbot.urls')),      # AI 聊天機器人
    path('i18n/', include('django.conf.urls.i18n')),    # 多語系
]

# 開發模式下提供媒體檔案
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

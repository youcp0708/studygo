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
    # API 路由：   /api/users/
    path('',        include('users.urls')),
    path('api/',    include('users.api_urls')),

    # 流程模塊（模塊二）
    # API 路由：   /api/flows/
    path('api/',    include('flows.api_urls')),
]

# 開發模式下提供媒體檔案
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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

    # 模塊一：使用者管理
    path('',     include('users.urls')),
    path('api/', include('users.api_urls')),

    # 模塊二：流程與任務管理
    path('',     include('flow.urls')),
    path('api/', include('flow.api_urls')),
]

# 開發模式下提供媒體檔案
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

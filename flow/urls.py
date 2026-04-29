"""
flow/urls.py
前端頁面路由 — 掛載於 studygo/urls.py → path('', include('flow.urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    path('flow/', views.flow_page, name='flow_page'),
]

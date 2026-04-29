"""
chatbot/urls.py
AI 聊天機器人前端頁面與 API 路由。
"""

from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chatbot_page, name='page'),
    path('api/message/', views.chat_message_api, name='message_api'),
    path('api/history/', views.chat_history_api, name='history_api'),
    path('api/history/clear/', views.clear_history_api, name='clear_history_api'),
]

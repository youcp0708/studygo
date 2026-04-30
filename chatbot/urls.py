from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chatbot_page, name='page'),

    path('api/message/', views.chat_message_api, name='message_api'),
    path('api/session/create/', views.create_session_api, name='create_session_api'),
    path('api/session/rename/', views.rename_session_api, name='rename_session_api'),
    path('api/session/pin/', views.pin_session_api, name='pin_session_api'),
    path('api/session/delete/', views.delete_session_api, name='delete_session_api'),
]
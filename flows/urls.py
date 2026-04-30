from django.urls import path
from . import views

urlpatterns = [
    # 前端網頁路由
    path('my-tasks/', views.my_flows_page, name='my_flows'),
]

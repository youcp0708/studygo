from django.urls import path
from . import views

urlpatterns = [
    path('my-tasks/', views.my_flows_page, name='my_flows'),
]

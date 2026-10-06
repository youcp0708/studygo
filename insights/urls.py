"""
insights/urls.py
掛載於 studygo/urls.py → path('insights/', include('insights.urls'))
"""

from django.urls import path

from . import views

app_name = 'insights'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.tasks, name='tasks'),
    path('alerts/', views.alerts, name='alerts'),
    path('questions/', views.questions, name='questions'),
    path('ask/', views.ask, name='ask'),
    path('export/<str:name>.csv', views.export_csv, name='export'),
]

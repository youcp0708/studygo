"""
flow/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    path('steps/',                    views.get_flow_steps,       name='api_flow_steps'),
    path('steps/<int:step_id>/toggle/', views.toggle_step,        name='api_flow_toggle'),
    path('progress/',                 views.get_progress_summary, name='api_flow_progress'),
]
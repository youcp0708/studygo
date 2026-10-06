"""insights/apps.py"""
from django.apps import AppConfig


class InsightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insights'
    label = 'insights'
    verbose_name = 'Student Insights 校方數據分析'

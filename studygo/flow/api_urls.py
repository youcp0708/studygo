"""
flow/api_urls.py
API 路由 — 掛載於 studygo/urls.py → path('api/', include('flow.api_urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    # POST /api/flow/generate/         → 生成 / 重新生成個人化流程
    path('flow/generate/',              views.generate_flow_view,  name='api_flow_generate'),

    # GET  /api/flow/me/               → 取得完整流程 + 所有任務
    path('flow/me/',                    views.flow_me_view,         name='api_flow_me'),

    # GET  /api/flow/tasks/            → 任務清單（可過濾 status / category）
    path('flow/tasks/',                 views.task_list_view,       name='api_flow_tasks'),

    # PATCH /api/flow/tasks/<pk>/      → 更新任務（status / notes / due_date）
    path('flow/tasks/<int:pk>/',        views.task_update_view,     name='api_flow_task_update'),

    # GET  /api/flow/stats/            → 完成統計（供 dashboard 使用）
    path('flow/stats/',                 views.flow_stats_view,      name='api_flow_stats'),
]

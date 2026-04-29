"""
flows/api_urls.py
流程模塊 API 路由
掛載於 studygo/urls.py → path('api/', include('flows.api_urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── 流程階段 ──────────────────────────────────────
    # GET   /api/flows/stages/              → 取得所有流程階段與任務列表
    path('flows/stages/',               views.stage_list_view,          name='api_flow_stages'),

    # ── 學生任務 ──────────────────────────────────────
    # POST  /api/flows/my-tasks/init/       → 初始化個人化任務清單
    path('flows/my-tasks/init/',        views.init_student_tasks_view,  name='api_init_tasks'),

    # GET   /api/flows/my-tasks/            → 取得我的任務清單（含進度）
    path('flows/my-tasks/',             views.my_tasks_view,            name='api_my_tasks'),

    # PATCH /api/flows/my-tasks/<id>/update/ → 更新某個任務的狀態
    path('flows/my-tasks/<int:task_id>/update/',
         views.update_task_status_view,  name='api_update_task'),

    # ── 進度總覽 ──────────────────────────────────────
    # GET   /api/flows/progress/            → 取得進度總覽（依階段分組）
    path('flows/progress/',             views.progress_overview_view,   name='api_progress'),

    # ── 提醒 ─────────────────────────────────────────
    # GET   /api/flows/reminders/           → 取得我的提醒列表
    path('flows/reminders/',            views.reminder_list_view,       name='api_reminders'),

    # POST  /api/flows/reminders/           → 新增提醒
    path('flows/reminders/create/',     views.create_reminder_view,     name='api_create_reminder'),

    # PATCH /api/flows/reminders/<id>/read/ → 標記提醒為已讀
    path('flows/reminders/<int:reminder_id>/read/',
         views.mark_reminder_read_view,  name='api_reminder_read'),
]

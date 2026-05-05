"""
flow/views.py
模塊二：流程與任務管理 API
"""

import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import FlowStepTemplate, ProcessFlow, UserTask
from .serializers import ProcessFlowSerializer, UserTaskSerializer, UpdateTaskSerializer

logger = logging.getLogger(__name__)


# ── Helpers（與 users/views.py 共用格式）────────────────────────
def success_response(data=None, message='成功', status_code=200):
    return Response({'success': True, 'message': message, 'data': data or {}},
                    status=status_code)

def error_response(message='發生錯誤', errors=None, status_code=400):
    return Response({'success': False, 'message': message, 'errors': errors or {}},
                    status=status_code)


# ══════════════════════════════════════════
# CORE: 根據 StudentProfile 生成個人化流程
# ══════════════════════════════════════════
def generate_flow_for_user(user):
    """
    根據使用者的 StudentProfile 生成（或更新）個人化任務清單。
    - 已完成的任務不會被覆蓋
    - 新增的模板任務才會被實例化
    回傳 ProcessFlow 實例。
    """
    profile = user.student_profile

    flow, _ = ProcessFlow.objects.get_or_create(
        user=user,
        defaults={
            'identity_type':    profile.identity_type,
            'admission_status': profile.admission_status,
        },
    )
    # 同步最新的 profile 快照
    flow.identity_type    = profile.identity_type
    flow.admission_status = profile.admission_status
    flow.save(update_fields=['identity_type', 'admission_status', 'updated_at'])

    # 找出適用的模板
    templates   = FlowStepTemplate.objects.filter(is_active=True)
    applicable  = [t for t in templates
                   if t.applies_to(profile.identity_type, profile.admission_status)]

    # 找出已存在的模板 ID（避免重複建立）
    existing_ids = set(
        flow.tasks.filter(template__isnull=False)
                  .values_list('template_id', flat=True)
    )

    new_tasks = []
    for tmpl in applicable:
        if tmpl.id in existing_ids:
            continue

        due_date = None
        if tmpl.days_offset is not None and profile.expected_arrival:
            due_date = profile.expected_arrival + timedelta(days=tmpl.days_offset)

        new_tasks.append(UserTask(
            user         = user,
            process_flow = flow,
            template     = tmpl,
            title        = tmpl.title,
            description  = tmpl.description,
            category     = tmpl.category,
            is_required  = tmpl.is_required,
            order        = tmpl.order,
            due_date     = due_date,
        ))

    if new_tasks:
        UserTask.objects.bulk_create(new_tasks)
        logger.info('為 %s 新增 %d 筆任務', user.email, len(new_tasks))

    return flow


# ══════════════════════════════════════════
# 1. 生成 / 重新生成個人化流程
# POST /api/flow/generate/
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_flow_view(request):
    user = request.user
    if not hasattr(user, 'student_profile'):
        return error_response('請先完成個人資料設定', status_code=400)

    flow = generate_flow_for_user(user)
    return success_response(
        ProcessFlowSerializer(flow).data,
        '個人化流程已生成'
    )


# ══════════════════════════════════════════
# 2. 取得目前使用者的流程與任務清單
# GET /api/flow/me/
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flow_me_view(request):
    try:
        flow = ProcessFlow.objects.prefetch_related('tasks').get(user=request.user)
    except ProcessFlow.DoesNotExist:
        return error_response('尚未生成流程，請完成個人資料後觸發生成', status_code=404)

    return success_response(ProcessFlowSerializer(flow).data)


# ══════════════════════════════════════════
# 3. 任務清單（支援過濾）
# GET /api/flow/tasks/?status=todo&category=visa
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_list_view(request):
    qs = UserTask.objects.filter(user=request.user)

    status_filter   = request.query_params.get('status')
    category_filter = request.query_params.get('category')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if category_filter:
        qs = qs.filter(category=category_filter)

    return success_response(UserTaskSerializer(qs, many=True).data)


# ══════════════════════════════════════════
# 4. 更新單一任務
# PATCH /api/flow/tasks/<pk>/
# ══════════════════════════════════════════
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def task_update_view(request, pk):
    try:
        task = UserTask.objects.get(pk=pk, user=request.user)
    except UserTask.DoesNotExist:
        return error_response('任務不存在', status_code=404)

    serializer = UpdateTaskSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response('資料驗證失敗', serializer.errors)

    data = serializer.validated_data

    if 'status' in data:
        new_status = data['status']
        if new_status == 'done' and task.status != 'done':
            task.completed_at = timezone.now()
        elif new_status != 'done':
            task.completed_at = None
        task.status = new_status

    if 'notes' in data:
        task.notes = data['notes']

    if 'due_date' in data:
        task.due_date = data['due_date']

    task.save()
    return success_response(UserTaskSerializer(task).data, '任務已更新')


# ══════════════════════════════════════════
# 5. 完成統計（供 dashboard 使用）
# GET /api/flow/stats/
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flow_stats_view(request):
    try:
        flow = ProcessFlow.objects.get(user=request.user)
    except ProcessFlow.DoesNotExist:
        return success_response({'has_flow': False, 'completion_rate': 0,
                                 'total': 0, 'done': 0, 'overdue_count': 0,
                                 'upcoming_tasks': []})

    total   = flow.tasks.count()
    done    = flow.tasks.filter(status='done').count()
    in_prog = flow.tasks.filter(status='in_progress').count()
    overdue = flow.tasks.filter(
        status__in=['todo', 'in_progress'],
        due_date__lt=timezone.now().date(),
    ).count()
    upcoming = flow.tasks.filter(
        status__in=['todo', 'in_progress'],
        due_date__gte=timezone.now().date(),
    ).order_by('due_date')[:5]

    return success_response({
        'has_flow':        True,
        'total':           total,
        'done':            done,
        'in_progress':     in_prog,
        'todo':            total - done - in_prog,
        'completion_rate': flow.completion_rate,
        'overdue_count':   overdue,
        'upcoming_tasks':  UserTaskSerializer(upcoming, many=True).data,
    })


# ══════════════════════════════════════════
# GUIDE: 僑生辦理居留證指南
# GET /flow/guide/arc-overseas/
# ══════════════════════════════════════════
def guide_arc_overseas(request):
    from django.shortcuts import render, redirect
    if not request.user.is_authenticated:
        return redirect('login_page')
    return render(request, 'flow/guide_arc_overseas.html')


def guide_arc_foreign(request):
    from django.shortcuts import render, redirect
    if not request.user.is_authenticated:
        return redirect('login_page')
    return render(request, 'flow/guide_arc_foreign.html')


def guide_arc_exchange(request):
    from django.shortcuts import render, redirect
    if not request.user.is_authenticated:
        return redirect('login_page')
    return render(request, 'flow/guide_arc_exchange.html')


# ══════════════════════════════════════════
# PAGE VIEW（返回 HTML 模板）
# GET /flow/
# ══════════════════════════════════════════
def flow_page(request):
    from django.shortcuts import render, redirect

    if not request.user.is_authenticated:
        return redirect('login_page')

    context = {'user': request.user}

    if hasattr(request.user, 'student_profile'):
        context['profile'] = request.user.student_profile
        try:
            flow = ProcessFlow.objects.prefetch_related('tasks').get(user=request.user)
            context['flow']  = flow
            context['tasks'] = flow.tasks.all()
        except ProcessFlow.DoesNotExist:
            context['flow']  = None
            context['tasks'] = []
    else:
        context['flow']  = None
        context['tasks'] = []

    return render(request, 'flow/flow.html', context)

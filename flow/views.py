"""
flow/views.py
模塊二：流程模塊 API
"""

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import FlowStep, UserProgress


# ══════════════════════════════════════════
# 1. 取得個人化流程步驟
# GET /api/flow/steps/
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_flow_steps(request):
    """
    根據使用者身份別，取得對應的流程步驟
    """
    user = request.user
    identity_type = 'all'

    if hasattr(user, 'student_profile'):
        identity_type = user.student_profile.identity_type

    # 取得適用的步驟（全部 + 該身份專屬）
    steps = FlowStep.objects.filter(
        is_active=True
    ).filter(
        identity_type__in=['all', identity_type]
    ).order_by('category', 'order')

    # 取得該使用者的進度
    progress_map = {
        p.step_id: p
        for p in UserProgress.objects.filter(user=user)
    }

    # 組合資料
    data = []
    for step in steps:
        progress = progress_map.get(step.id)
        data.append({
            'id':           step.id,
            'title':        step.title,
            'description':  step.description,
            'category':     step.category,
            'category_display': step.get_category_display(),
            'identity_type': step.identity_type,
            'order':        step.order,
            'deadline_days': step.deadline_days,
            'is_done':      progress.is_done if progress else False,
            'done_at':      progress.done_at if progress else None,
            'note':         progress.note if progress else '',
        })

    return Response({'success': True, 'data': data})


# ══════════════════════════════════════════
# 2. 標記步驟完成/未完成
# POST /api/flow/steps/<step_id>/toggle/
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_step(request, step_id):
    """
    切換步驟完成狀態
    """
    try:
        step = FlowStep.objects.get(id=step_id, is_active=True)
    except FlowStep.DoesNotExist:
        return Response({'success': False, 'message': '步驟不存在'}, status=404)

    progress, _ = UserProgress.objects.get_or_create(
        user=request.user,
        step=step,
    )

    # 切換完成狀態
    progress.is_done = not progress.is_done
    progress.done_at = timezone.now() if progress.is_done else None
    progress.save()

    return Response({
        'success': True,
        'message': '已標記完成' if progress.is_done else '已取消完成',
        'data': {
            'step_id': step.id,
            'is_done': progress.is_done,
            'done_at': progress.done_at,
        }
    })


# ══════════════════════════════════════════
# 3. 取得進度統計
# GET /api/flow/progress/
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_progress_summary(request):
    """
    取得使用者的整體完成進度
    """
    user = request.user
    identity_type = 'all'

    if hasattr(user, 'student_profile'):
        identity_type = user.student_profile.identity_type

    total = FlowStep.objects.filter(
        is_active=True,
        identity_type__in=['all', identity_type]
    ).count()

    done = UserProgress.objects.filter(
        user=user,
        is_done=True
    ).count()

    percent = round((done / total * 100) if total > 0 else 0)

    return Response({
        'success': True,
        'data': {
            'total':   total,
            'done':    done,
            'percent': percent,
        }
    })
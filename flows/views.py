"""
flows/views.py
流程模塊 API Views
"""

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import StudentProfile
from .models import FlowStage, Task, StudentTask, Reminder
from .serializers import (
    FlowStageSerializer,
    TaskSerializer,
    StudentTaskSerializer,
    ReminderSerializer,
)


# ══════════════════════════════════════════
# HELPER（與 users/views.py 保持一致的回應格式）
# ══════════════════════════════════════════
def success_response(data=None, message='成功', status_code=200):
    return Response({'success': True, 'message': message, 'data': data or {}},
                    status=status_code)

def error_response(message='發生錯誤', errors=None, status_code=400):
    return Response({'success': False, 'message': message, 'errors': errors or {}},
                    status=status_code)


# ══════════════════════════════════════════
# 1. 取得所有流程階段與任務
# GET /api/flows/stages/
#
# 功能說明：
#   回傳系統中所有的流程階段（例如：來台前、抵台後、入學報到），
#   每個階段底下會附帶它包含的所有任務。
#   這是給前端「流程總覽頁面」用的。
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stage_list_view(request):
    """
    Response (200):
      { "success": true,
        "data": [
          { "id": 1, "name": "來台前", "order": 1,
            "tasks": [ { "id": 1, "title": "申請簽證", ... }, ... ]
          }, ...
        ] }
    """
    stages = FlowStage.objects.prefetch_related('tasks').all()
    serializer = FlowStageSerializer(stages, many=True)
    return success_response(serializer.data)


# ══════════════════════════════════════════
# 2. 初始化學生的個人化任務清單
# POST /api/flows/my-tasks/init/
#
# 功能說明：
#   根據學生的身份別、國籍、入學狀態，
#   從「任務模板 (Task)」中篩選出適合這位學生的任務，
#   然後在「學生任務進度 (StudentTask)」中幫他建立記錄。
#   這樣每位學生就有自己專屬的待辦事項清單。
#
#   篩選邏輯：
#   - 如果任務的「適用身份別」欄位是空的 → 代表全部身份別都適用
#   - 如果任務的「適用身份別」和學生的身份別相符 → 也適用
#   - 國籍和入學狀態也是同樣的邏輯
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def init_student_tasks_view(request):
    """
    Response (201):
      { "success": true, "message": "已為您生成 12 項個人化任務",
        "data": { "created_count": 12, "skipped_count": 3 } }
    """
    user = request.user

    # 檢查學生是否已建立 StudentProfile
    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料（POST /api/users/profile/）', status_code=400)

    # 取得所有任務模板
    all_tasks = Task.objects.all()

    created_count = 0
    skipped_count = 0

    for task in all_tasks:
        # ── 篩選邏輯：欄位為空代表「不限」，全部適用 ──
        if task.identity_type and task.identity_type != profile.identity_type:
            skipped_count += 1
            continue
        if task.nationality and task.nationality != profile.nationality:
            skipped_count += 1
            continue
        if task.admission_status and task.admission_status != profile.admission_status:
            skipped_count += 1
            continue

        # 避免重複建立（unique_together: student + task）
        _, created = StudentTask.objects.get_or_create(
            student=profile,
            task=task,
        )
        if created:
            created_count += 1

    return success_response({
        'created_count': created_count,
        'skipped_count': skipped_count,
    }, f'已為您生成 {created_count} 項個人化任務', status_code=201)


# ══════════════════════════════════════════
# 3. 取得學生自己的任務清單（含進度）
# GET /api/flows/my-tasks/
#
# 功能說明：
#   回傳這位學生所有的任務和進度狀態。
#   前端可以用這個 API 畫出學生的「個人待辦清單」。
#   每個任務都會附帶：任務詳細資料、狀態中文名、提醒資料。
#
#   支援篩選參數：
#   - ?status=completed    → 只看已完成的任務
#   - ?stage=1             → 只看某個階段的任務
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_tasks_view(request):
    """
    Response (200):
      { "success": true,
        "data": {
          "tasks": [ { "id": 1, "status": "not_started",
                       "status_display": "未開始",
                       "task_detail": { "title": "申請簽證", ... },
                       "reminders": [...] }, ... ],
          "summary": { "total": 12, "completed": 3, "progress_percent": 25 }
        } }
    """
    user = request.user

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)

    # 基本查詢
    qs = StudentTask.objects.filter(student=profile) \
        .select_related('task', 'task__stage') \
        .prefetch_related('reminders')

    # ── 篩選功能 ──
    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    stage_filter = request.query_params.get('stage')
    if stage_filter:
        qs = qs.filter(task__stage_id=stage_filter)

    # 依照流程階段排序 → 任務排序
    qs = qs.order_by('task__stage__order', 'task__order')

    serializer = StudentTaskSerializer(qs, many=True)

    # ── 計算進度摘要 ──
    all_tasks = StudentTask.objects.filter(student=profile)
    total = all_tasks.count()
    completed = all_tasks.filter(status='completed').count()
    progress = round((completed / total * 100), 1) if total > 0 else 0

    return success_response({
        'tasks': serializer.data,
        'summary': {
            'total': total,
            'completed': completed,
            'in_progress': all_tasks.filter(status='in_progress').count(),
            'not_started': all_tasks.filter(status='not_started').count(),
            'progress_percent': progress,
        },
    })


# ══════════════════════════════════════════
# 4. 更新任務狀態（打勾完成 / 更改進度）
# PATCH /api/flows/my-tasks/<id>/update/
#
# 功能說明：
#   學生可以更新自己的任務狀態。
#   例如把「未開始」改成「進行中」，或是標記為「已完成」。
#   當狀態改為「已完成」時，系統會自動記錄完成時間。
# ══════════════════════════════════════════
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_task_status_view(request, task_id):
    """
    Request Body:
      { "status": "completed" }

    Response (200):
      { "success": true, "message": "任務狀態更新成功" }
    """
    user = request.user

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)

    try:
        student_task = StudentTask.objects.get(id=task_id, student=profile)
    except StudentTask.DoesNotExist:
        return error_response('找不到此任務或無權限操作', status_code=404)

    new_status = request.data.get('status')
    valid_statuses = [c[0] for c in StudentTask.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return error_response(
            f'無效的狀態，可選值：{", ".join(valid_statuses)}',
            status_code=400
        )

    student_task.status = new_status

    # 如果標記為「已完成」，自動記錄完成時間
    if new_status == 'completed':
        student_task.completed_at = timezone.now()
    else:
        student_task.completed_at = None  # 取消完成時清除時間

    student_task.save()

    return success_response(
        StudentTaskSerializer(student_task).data,
        '任務狀態更新成功'
    )


# ══════════════════════════════════════════
# 5. 取得學生的提醒列表
# GET /api/flows/reminders/
#
# 功能說明：
#   回傳這位學生所有任務的提醒通知。
#   支援篩選：
#   - ?unread=true  → 只看未讀的提醒
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reminder_list_view(request):
    """
    Response (200):
      { "success": true,
        "data": { "reminders": [...], "unread_count": 3 } }
    """
    user = request.user

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)

    qs = Reminder.objects.filter(student_task__student=profile) \
        .select_related('student_task', 'student_task__task')

    # 篩選未讀
    if request.query_params.get('unread') == 'true':
        qs = qs.filter(is_read=False)

    serializer = ReminderSerializer(qs, many=True)
    unread_count = Reminder.objects.filter(
        student_task__student=profile, is_read=False
    ).count()

    return success_response({
        'reminders': serializer.data,
        'unread_count': unread_count,
    })


# ══════════════════════════════════════════
# 6. 新增提醒
# POST /api/flows/reminders/
#
# 功能說明：
#   為某個學生任務新增一筆提醒。
#   例如：「記得在 5/15 前去辦理居留證」。
# ══════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reminder_view(request):
    """
    Request Body:
      { "student_task": 1, "message": "5/15 前辦理居留證",
        "remind_date": "2026-05-15" }

    Response (201):
      { "success": true, "message": "提醒建立成功" }
    """
    user = request.user

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)

    # 確認這個 student_task 是屬於當前學生的
    student_task_id = request.data.get('student_task')
    try:
        student_task = StudentTask.objects.get(id=student_task_id, student=profile)
    except StudentTask.DoesNotExist:
        return error_response('找不到此任務或無權限操作', status_code=404)

    serializer = ReminderSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response('資料驗證失敗', serializer.errors)

    serializer.save()
    return success_response(serializer.data, '提醒建立成功', status_code=201)


# ══════════════════════════════════════════
# 7. 標記提醒為已讀
# PATCH /api/flows/reminders/<id>/read/
#
# 功能說明：
#   學生點擊提醒後，把它標記為「已讀」。
# ══════════════════════════════════════════
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_reminder_read_view(request, reminder_id):
    """
    Response (200):
      { "success": true, "message": "已標記為已讀" }
    """
    user = request.user

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)

    try:
        reminder = Reminder.objects.get(
            id=reminder_id,
            student_task__student=profile
        )
    except Reminder.DoesNotExist:
        return error_response('找不到此提醒或無權限操作', status_code=404)

    reminder.is_read = True
    reminder.save(update_fields=['is_read'])

    return success_response(message='已標記為已讀')


# ══════════════════════════════════════════
# 8. 取得進度總覽（依階段分組）
# GET /api/flows/progress/
#
# 功能說明：
#   回傳「每個流程階段」的完成度，讓前端可以畫出進度條。
#   例如：來台前 75%、抵台後 20%、入學報到 0%
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progress_overview_view(request):
    """
    Response (200):
      { "success": true,
        "data": {
          "overall_percent": 35.5,
          "stages": [
            { "stage_id": 1, "stage_name": "來台前",
              "total": 4, "completed": 3, "percent": 75.0 },
            ...
          ]
        } }
    """
    user = request.user

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)

    stages = FlowStage.objects.all().order_by('order')
    stage_data = []
    overall_total = 0
    overall_completed = 0

    for stage in stages:
        tasks_in_stage = StudentTask.objects.filter(
            student=profile, task__stage=stage
        )
        total = tasks_in_stage.count()
        completed = tasks_in_stage.filter(status='completed').count()
        percent = round((completed / total * 100), 1) if total > 0 else 0

        overall_total += total
        overall_completed += completed

        stage_data.append({
            'stage_id': stage.id,
            'stage_name': stage.name,
            'total': total,
            'completed': completed,
            'percent': percent,
        })

    overall_percent = round(
        (overall_completed / overall_total * 100), 1
    ) if overall_total > 0 else 0

    return success_response({
        'overall_percent': overall_percent,
        'stages': stage_data,
    })

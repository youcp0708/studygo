"""
flows/views.py
流程模塊 API Views
"""

from django.utils import timezone
from django.utils.translation import get_language
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import StudentProfile


# ==========================================
# 前端網頁視圖 (Web Views)
# ==========================================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect

@login_required(login_url='/login/')
def my_flows_page(request):
    """
    渲染個人的「任務清單」頁面
    """
    if not hasattr(request.user, 'student_profile'):
        return redirect('profile_setup')
    profile = request.user.student_profile
    unread_count = profile.reminders.filter(
        is_read=False
    ).count()
    return render(request, 'flows/my_flows.html', {
        'unread_count': unread_count,
    })


@login_required(login_url='/login/')
def guide_index(request):
    return render(request, 'flows/guide_index.html')

@login_required(login_url='/login/')
def guide_regulations(request):
    return render(request, 'flows/guide_regulations.html')

@login_required(login_url='/login/')
def admissions_guide(request):
    return render(request, 'flows/admissions_guide.html')

@login_required(login_url='/login/')
def guide_arc_exchange(request):
    return render(request, 'flows/guide_arc_exchange.html')

@login_required(login_url='/login/')
def guide_arc_foreign(request):
    return render(request, 'flows/guide_arc_foreign.html')

@login_required(login_url='/login/')
def guide_arc_overseas(request):
    return render(request, 'flows/guide_arc_overseas.html')

@login_required(login_url='/login/')
def guide_bus_ncu(request):
    return render(request, 'flows/guide_bus_ncu.html')

@login_required(login_url='/login/')
def guide_housing_ncu(request):
    return render(request, 'flows/guide_housing_ncu.html')

@login_required(login_url='/login/')
def guide_nhi(request):
    return render(request, 'flows/guide_nhi.html')

@login_required(login_url='/login/')
def guide_bank(request):
    return render(request, 'flows/guide_bank.html')

@login_required(login_url='/login/')
def guide_sim(request):
    return render(request, 'flows/guide_sim.html')


# ==========================================
# REST API 視圖 (DRF)
# ==========================================
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
    同步學生的個人化任務清單：
    - 新增符合條件但尚未建立的任務
    - 刪除不再符合條件的舊任務（例如 admin 更新了任務的限定條件）

    Response (201):
      { "success": true, "message": "同步完成：新增 3 項，移除 1 項",
        "data": { "created_count": 3, "removed_count": 1 } }
    """
    user = request.user

    # 檢查學生是否已建立 StudentProfile
    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料（POST /api/users/profile/）', status_code=400)

    all_tasks = Task.objects.all()

    # ── 計算哪些任務符合此學生的條件 ──
    eligible_task_ids = set()
    for task in all_tasks:
        if task.region and profile.region not in task.region:
            continue
        if task.identity_type and profile.identity_type not in task.identity_type:
            continue
        if task.nationality and profile.nationality not in task.nationality:
            continue
        if task.university and task.university != profile.university:
            continue
        if task.admission_status and task.admission_status != profile.admission_status:
            continue
        eligible_task_ids.add(task.id)

    # ── 取得目前學生已有的任務 ──
    existing_student_tasks = StudentTask.objects.filter(student=profile)
    existing_task_ids = set(existing_student_tasks.values_list('task_id', flat=True))

    # ── 1. 移除不再符合條件的舊任務 ──
    to_remove_ids = existing_task_ids - eligible_task_ids
    removed_count = 0
    if to_remove_ids:
        removed_count, _ = StudentTask.objects.filter(
            student=profile, task_id__in=to_remove_ids
        ).delete()

    # ── 2. 新增符合條件但尚未建立的任務 ──
    to_create_ids = eligible_task_ids - existing_task_ids
    created_count = 0
    for task_id in to_create_ids:
        StudentTask.objects.create(student=profile, task_id=task_id)
        created_count += 1

    return success_response({
        'created_count': created_count,
        'removed_count': removed_count,
    }, f'同步完成：新增 {created_count} 項，移除 {removed_count} 項', status_code=201)


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
          "stages": [
             { "stage_id": 1, "stage_name": "來台前", "tasks": [ ...StudentTaskSerializer... ] }
          ],
          "summary": { "total": 12, "completed": 3, "progress_percent": 25 }
        } }
    """
    user = request.user

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)

    # ── 篩選功能 ──
    status_filter = request.query_params.get('status')
    stage_filter = request.query_params.get('stage')

    stages = FlowStage.objects.all().order_by('order')
    if stage_filter:
        stages = stages.filter(id=stage_filter)

    stages_data = []
    
    for stage in stages:
        qs = StudentTask.objects.filter(student=profile, task__stage=stage) \
            .select_related('task') \
            .order_by('task__order')
            
        if status_filter:
            qs = qs.filter(status=status_filter)
            
        if qs.exists():
            tasks_data = []
            # ── 取得目前請求的語言（Django 語言切換 cookie），優先於資料庫欄位 ──
            active_lang = get_language() or ''  # e.g. 'my', 'en', 'zh-hant'
            # 取短代碼：'zh-hant' → 'zh', 'my' → 'my'
            short_lang = active_lang.split('-')[0] if '-' in active_lang else active_lang
            # get_localized 支援 en/my/id/ms/th/ja，其他回退中文
            SUPPORTED = {'en', 'my', 'id', 'ms', 'th', 'ja', 'ko'}
            if short_lang not in SUPPORTED:
                short_lang = ''  # 空字串 = 使用中文預設
            print(f"[DEBUG] get_language()={active_lang!r}, short_lang={short_lang!r}")

            for st in qs:
                task_data = StudentTaskSerializer(st).data
                t = st.task

                # ── 本地化的文字欄位 ──
                localized = t.get_localized(short_lang)

                # ── 期限資訊（使用本地化的 deadline_text）──
                dl_type = t.deadline_type
                dl_text = localized['deadline_text']
                calculated_due_date = None
                arrival_missing = False

                if dl_type == 'from_arrival':
                    if profile.expected_arrival and t.deadline_days is not None:
                        from datetime import timedelta
                        calculated_due_date = (
                            profile.expected_arrival + timedelta(days=t.deadline_days)
                        ).strftime('%Y/%m/%d')
                    else:
                        arrival_missing = True

                task_data['localized'] = localized
                task_data['deadline_info'] = {
                    'type': dl_type,
                    'text': dl_text,
                    'calculated_due_date': calculated_due_date,
                    'arrival_missing': arrival_missing,
                }
                tasks_data.append(task_data)

            stages_data.append({
                'stage_id': stage.id,
                'stage_name': stage.get_name_by_lang(short_lang),
                'tasks': tasks_data
            })

    # ── 計算進度摘要 ──
    all_tasks = StudentTask.objects.filter(student=profile)
    total = all_tasks.count()
    completed = all_tasks.filter(status='completed').count()
    progress = round((completed / total * 100), 1) if total > 0 else 0

    return success_response({
        'stages': stages_data,
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

    if 'status' in request.data:
        new_status = request.data.get('status')
        valid_statuses = [c[0] for c in StudentTask.STATUS_CHOICES]
        if new_status in valid_statuses:
            student_task.status = new_status
            if new_status == 'completed':
                student_task.completed_at = timezone.now()
            else:
                student_task.completed_at = None

    if 'note' in request.data:
        student_task.note = request.data.get('note')

    student_task.save()

    return success_response(
        StudentTaskSerializer(student_task).data,
        '任務更新成功'
    )


# ══════════════════════════════════════════
# 5. 批量更新任務狀態
# PATCH /api/flows/my-tasks/bulk/
# ══════════════════════════════════════════
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def bulk_update_task_status_view(request):
    """
    Request Body:
      {
        "task_ids": [1, 2, 3],
        "action": "complete"  # or "not_started", "in_progress"
      }
    """
    user = request.user

    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)

    task_ids = request.data.get('task_ids', [])
    action = request.data.get('action')

    if not task_ids or not isinstance(task_ids, list):
        return error_response('請提供 task_ids 陣列', status_code=400)

    if action not in ['complete', 'not_started', 'in_progress']:
        return error_response('無效的操作', status_code=400)

    status_map = {
        'complete': 'completed',
        'not_started': 'not_started',
        'in_progress': 'in_progress'
    }
    
    new_status = status_map[action]

    tasks = StudentTask.objects.filter(id__in=task_ids, student=profile)
    updated_count = 0

    for task in tasks:
        task.status = new_status
        if new_status == 'completed':
            task.completed_at = timezone.now()
        else:
            task.completed_at = None
        task.save()
        updated_count += 1

    return success_response(
        {'updated_count': updated_count},
        f'成功更新 {updated_count} 筆任務'
    )





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

    active_lang = get_language() or ''
    short_lang = active_lang.split('-')[0] if '-' in active_lang else active_lang
    SUPPORTED = {'en', 'my', 'id', 'ms', 'th', 'ja', 'ko'}
    if short_lang not in SUPPORTED:
        short_lang = ''
        
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
            'stage_name': stage.get_name_by_lang(short_lang),
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


# ══════════════════════════════════════════
# 9. 取得使用者的提醒列表
# GET /api/flows/reminders/
# ══════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reminders_view(request):
    user = request.user
    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)
        
    reminders = profile.reminders.all()
    
    # 可支援只抓未讀
    if request.query_params.get('unread_only') == 'true':
        reminders = reminders.filter(is_read=False)
        
    serializer = ReminderSerializer(reminders, many=True)
    return success_response({
        'reminders': serializer.data,
        'unread_count': profile.reminders.filter(is_read=False).count()
    })

# ══════════════════════════════════════════
# 10. 標記提醒為已讀
# PATCH /api/flows/reminders/<id>/read/
# ══════════════════════════════════════════
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def read_reminder_view(request, reminder_id):
    user = request.user
    try:
        profile = user.student_profile
    except StudentProfile.DoesNotExist:
        return error_response('請先建立學生資料', status_code=400)
        
    try:
        reminder = profile.reminders.get(id=reminder_id)
    except Exception:
        return error_response('找不到此提醒', status_code=404)
        
    reminder.is_read = True
    reminder.save()
    
    return success_response({}, '已標記為已讀')

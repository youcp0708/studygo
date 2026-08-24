from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.clickjacking import xframe_options_sameorigin
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ChatSession, ChatMessage, ChatAttachment, ChatFeedback, ALLOWED_ATTACHMENT_EXTENSIONS
from .services import (
    generate_ai_reply, contains_crisis_keywords, build_crisis_resources,
    get_guide_page_for_task, create_welcome_chat_messages,
)
from django.utils import timezone
from django.utils.translation import gettext as _

import logging
import uuid

logger = logging.getLogger(__name__)

MAX_ATTACHMENT_SIZE = 8 * 1024 * 1024  # 8MB，低於 settings.DATA_UPLOAD_MAX_MEMORY_SIZE


def normalize_ai_mode(value):
    value = value or "helper"
    if value not in ["helper", "friend"]:
        return "helper"
    return value


def get_taiwan_tips():
    return [
        _("台灣的便利商店可以繳費、取貨、影印，也能買到很多生活用品。"),
        _("在台灣搭捷運、公車，常會使用悠遊卡或一卡通。"),
        _("台灣很多學校都有國際事務處，可以協助境外生處理入學與生活問題。"),
        _("在台灣租屋前，建議先確認租金、押金、水電費和租約期限。"),
        _("台灣看醫生時，如果已加入健保，通常醫療費用會比自費便宜。"),
        _("台灣垃圾車通常會播放音樂提醒居民倒垃圾，不同地區時間不同。"),
        _("台灣夏天較熱且潮濕，外出可以準備水壺、防曬和雨具。"),
        _("如果在台灣變更住址，部分證件或學校資料可能需要一起更新。"),
        _("台灣校園常用 Email 或學校系統公告重要資訊，建議定期查看。"),
        _("來台後辦理手機門號時，通常需要護照、居留證或其他身分文件。"),
    ]


def get_daily_taiwan_tip():
    tips = get_taiwan_tips()
    today = timezone.localdate()
    index = today.toordinal() % len(tips)
    return tips[index]


@xframe_options_sameorigin  # 允許聊天頁被同源 iframe（浮動小工具）嵌入，仍防跨站點擊劫持
@login_required(login_url='/login/')
@ensure_csrf_cookie
def chatbot_page(request):
    """
    聊天頁面：
    - 左邊顯示目前 AI 模式的聊天記錄
    - 有 ?session=xx 時載入該對話，並以該 session 的 ai_mode 為目前模式
    - 沒有 session 時根據 ?ai_mode=helper/friend 顯示空白歡迎頁
    """
    requested_ai_mode = normalize_ai_mode(request.GET.get("ai_mode", "helper"))

    session_id = request.GET.get('session')
    active_session = None
    messages = []
    current_ai_mode = requested_ai_mode

    if session_id:
        active_session = ChatSession.objects.filter(
            id=session_id,
            user=request.user
        ).first()

        if active_session:
            current_ai_mode = normalize_ai_mode(getattr(active_session, "ai_mode", "helper"))
            messages = active_session.messages.all().prefetch_related('attachments')

    sessions = ChatSession.objects.filter(
        user=request.user,
        ai_mode=current_ai_mode
    ).order_by('-is_pinned', '-updated_at')

    context = {
        'user': request.user,
        'profile': getattr(request.user, 'student_profile', None),
        'sessions': sessions,
        'active_session': active_session,
        'messages': messages,
        'current_ai_mode': current_ai_mode,
        "taiwan_tip": get_daily_taiwan_tip(),
        "taiwan_tips": get_taiwan_tips(),
        # embed=1：以浮動小工具（iframe）方式載入，隱藏站台導覽列與頁尾
        'embed': request.GET.get('embed') == '1',
    }

    return render(request, 'chatbot/chatbot.html', context)


def split_friend_reply(reply):
    import re
    reply = (reply or '').strip()

    if not reply:
        return []

    # 在句尾標點後切割（保留標點在前一句）
    parts = re.split(r'(?<=[。！？])\s*', reply)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= 1:
        return [reply]

    # 最多 2 則，超過就把剩餘合併進最後一則
    if len(parts) > 2:
        parts = parts[:1] + [''.join(parts[1:])]

    return parts

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_message_api(request):
    """
    POST /chatbot/api/message/
    """
    message = (request.data.get('message') or '').strip()

    ai_mode = normalize_ai_mode(request.data.get("ai_mode", "helper"))
    session_id = request.data.get('session_id')
    role = (request.data.get('role') or '').strip()
    personality = (request.data.get('personality') or '').strip()

    attachments = request.FILES.getlist('attachments')
    attachment_types = request.data.getlist('attachment_types')

    for uploaded_file in attachments:
        ext = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else ''
        if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
            return Response({
                'success': False,
                'message': f'不支援的檔案格式：{ext or uploaded_file.name}',
            }, status=status.HTTP_400_BAD_REQUEST)
        if uploaded_file.size > MAX_ATTACHMENT_SIZE:
            return Response({
                'success': False,
                'message': f'檔案 {uploaded_file.name} 超過大小上限（{MAX_ATTACHMENT_SIZE // (1024 * 1024)}MB）',
            }, status=status.HTTP_400_BAD_REQUEST)

    if not message and not attachments:
        return Response({
            'success': False,
            'message': '請輸入問題或上傳附件',
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(message) > 1200:
        return Response({
            'success': False,
            'message': '問題太長，請縮短到 1200 字以內',
        }, status=status.HTTP_400_BAD_REQUEST)

    if not message:
        message = '已上傳附件'

    session = None

    if session_id:
        session = ChatSession.objects.filter(
            id=session_id,
            user=request.user
        ).first()

    if session:
        # 防止前端傳錯模式時，把舊對話混到另一個 AI。
        ai_mode = normalize_ai_mode(getattr(session, "ai_mode", ai_mode))
    else:
        title = message[:24] + ('…' if len(message) > 24 else '')
        session = ChatSession.objects.create(
            user=request.user,
            title=title,
            ai_mode=ai_mode,
        )

    if ai_mode == 'friend':
        # friend 模式需要較多上下文，但仍設上限避免長對話 token 成本失控
        recent_messages = list(session.messages.order_by('-created_at')[:60])
        recent_messages.reverse()
    else:
        recent_messages = list(session.messages.order_by('-created_at')[:10])
        recent_messages.reverse()

    user_msg = ChatMessage.objects.create(
        session=session,
        role='user',
        content=message,
    )

    # 如果是新聊天，或標題還是預設值，就用使用者第一句話當聊天標題
    if session.title in ["新的聊天", "New Chat", "", None]:
        new_title = message.strip()
        if len(new_title) > 30:
            new_title = new_title[:30] + "..."
        session.title = new_title
        session.save(update_fields=["title", "updated_at"])

    created_attachments = []

    for index, uploaded_file in enumerate(attachments):
        attachment_type = 'file'

        if index < len(attachment_types):
            attachment_type = attachment_types[index]

        original_name = uploaded_file.name
        ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
        # 檔名可能含中文等非 ASCII 字元，Supabase S3 相容儲存的 HeadObject
        # 對這類 key 會回 400，所以實際存檔用安全的隨機檔名，原始檔名另外存 original_name 顯示用。
        uploaded_file.name = f'{uuid.uuid4().hex}.{ext}' if ext else uuid.uuid4().hex

        attachment = ChatAttachment.objects.create(
            message=user_msg,
            file=uploaded_file,
            attachment_type=attachment_type,
            original_name=original_name,
        )
        created_attachments.append(attachment)

    ai_result = generate_ai_reply(
        user=request.user,
        question=message,
        recent_messages=recent_messages,
        ai_mode=ai_mode,
        attachments=created_attachments,
        role=role,
        personality=personality,
    )

    logger.debug('ai_result source=%s model=%s', ai_result.get('source'), ai_result.get('model'))

    if ai_mode == "friend":
        reply_parts = split_friend_reply(ai_result['reply'])
        # 如果有真實地點搜尋結果，直接附加為獨立訊息，不依賴 AI 輸出
        place_text = ai_result.get('place_results_text')
        if place_text:
            reply_parts.append(place_text)

        # 天氣資料同理：真實數字直接附加為獨立訊息，不讓 AI 自己複述數字
        weather_text = ai_result.get('weather_results_text')
        if weather_text:
            reply_parts.append(weather_text)

        # 危機保底安全網：只要學生訊息命中危機關鍵字（9 語），
        # 且 AI 回覆沒有帶出可撥打的求助電話，就由伺服器端強制附上，
        # 不把學生的安全交給模型的自由發揮
        if contains_crisis_keywords(message):
            has_tel_link = any('tel:' in part for part in reply_parts)
            if not has_tel_link:
                reply_parts.append(build_crisis_resources(request.user))
    else:
        # 任務小幫手固定只回一則訊息，不像聊天好朋友那樣拆成多個泡泡；
        # 有查詢網頁時把來源接在同一則訊息末尾，而不是附成獨立訊息。
        # 由後端組裝而不是靠 AI 自己寫，可以確保來源網址不會被模型改寫或漏掉。
        reply_text = ai_result['reply']

        # 校內處室/系所/大樓的地圖連結同理：由後端直接附上真實查到的連結，
        # 不讓 AI 自己複述或編造地址與網址
        campus_place_text = ai_result.get('campus_place_results_text')
        if campus_place_text:
            reply_text = f"{reply_text}\n\n{campus_place_text}"

        citations_text = ai_result.get('citations_text')
        if citations_text:
            reply_text = f"{reply_text}\n\n{citations_text}"

        reply_parts = [reply_text]

    assistant_messages = []

    for part in reply_parts:
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=part,
        )

        assistant_messages.append({
            'id': assistant_msg.id,
            'role': assistant_msg.role,
            'content': assistant_msg.content,
            'created_at': assistant_msg.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    session.ai_mode = ai_mode
    session.save(update_fields=['ai_mode', 'updated_at'])

    return Response({
        'success': True,
        'message': 'AI 回覆成功',
        'data': {
            'session_id': session.id,
            'session_title': session.title,
            'is_pinned': session.is_pinned,
            'ai_mode': session.ai_mode,
            'user_message': {
            'id': user_msg.id,
            'role': user_msg.role,
            'content': user_msg.content,
            'created_at': user_msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'attachments': [
                {
                    'url': attachment.file.url,
                    'type': attachment.attachment_type,
                    'name': attachment.original_name,
                }
                for attachment in created_attachments
            ],
        },
        # 新版：多則 AI 訊息
        'assistant_messages': assistant_messages,

        # 「你可能還想問」追問建議（helper 模式，由知識庫標題生成）
        'suggestions': ai_result.get('suggestions', []),

        # 保留舊版欄位，避免前端其他地方壞掉
        'assistant_message': assistant_messages[0] if assistant_messages else None,
    }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session_api(request):
    ai_mode = normalize_ai_mode(request.data.get("ai_mode", "helper"))

    session = ChatSession.objects.create(
        user=request.user,
        title='新的聊天',
        ai_mode=ai_mode,
    )

    return Response({
        'success': True,
        'message': '建立新聊天成功',
        'data': {
            'session_id': session.id,
            'title': session.title,
            'ai_mode': session.ai_mode,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rename_session_api(request):
    session_id = request.data.get('session_id')
    title = (request.data.get('title') or '').strip()

    if not title:
        return Response({
            'success': False,
            'message': '請輸入新的聊天名稱',
        }, status=status.HTTP_400_BAD_REQUEST)

    session = ChatSession.objects.filter(
        id=session_id,
        user=request.user
    ).first()

    if not session:
        return Response({
            'success': False,
            'message': '找不到此聊天紀錄',
        }, status=status.HTTP_404_NOT_FOUND)

    session.title = title
    session.save(update_fields=['title', 'updated_at'])

    return Response({
        'success': True,
        'message': '重新命名成功',
        'data': {
            'title': session.title,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pin_session_api(request):
    session_id = request.data.get('session_id')

    session = ChatSession.objects.filter(
        id=session_id,
        user=request.user
    ).first()

    if not session:
        return Response({
            'success': False,
            'message': '找不到此聊天紀錄',
        }, status=status.HTTP_404_NOT_FOUND)

    session.is_pinned = not session.is_pinned
    session.save(update_fields=['is_pinned', 'updated_at'])

    return Response({
        'success': True,
        'message': '更新釘選成功',
        'data': {
            'is_pinned': session.is_pinned,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_api(request):
    """
    POST /chatbot/api/feedback/
    Body: { "message_id": 123, "rating": "up" | "down" }
    學生對 AI 回覆按 👍/👎，同一則訊息重複評價會覆蓋（可改變心意）。
    """
    message_id = request.data.get('message_id')
    rating = request.data.get('rating')

    if rating not in ['up', 'down']:
        return Response({
            'success': False,
            'message': '無效的評價',
        }, status=status.HTTP_400_BAD_REQUEST)

    message = ChatMessage.objects.filter(
        id=message_id,
        role='assistant',
        session__user=request.user,   # 只能評價自己對話中的訊息
    ).first()

    if not message:
        return Response({
            'success': False,
            'message': '找不到此訊息',
        }, status=status.HTTP_404_NOT_FOUND)

    feedback, _created = ChatFeedback.objects.update_or_create(
        message=message,
        defaults={'rating': rating},
    )

    return Response({
        'success': True,
        'message': '感謝你的回饋',
        'data': {'rating': feedback.rating},
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_session_api(request):
    session_id = request.data.get('session_id')

    session = ChatSession.objects.filter(
        id=session_id,
        user=request.user
    ).first()

    if not session:
        return Response({
            'success': False,
            'message': '找不到此聊天紀錄',
        }, status=status.HTTP_404_NOT_FOUND)

    ai_mode = normalize_ai_mode(getattr(session, "ai_mode", "helper"))

    session.delete()

    next_session = ChatSession.objects.filter(
        user=request.user,
        ai_mode=ai_mode,
    ).order_by('-is_pinned', '-updated_at').first()

    return Response({
        'success': True,
        'message': '刪除成功',
        'data': {
            'next_session_id': next_session.id if next_session else None
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_guide_view(request, student_task_id):
    """
    GET /chatbot/api/task-guide/<student_task_id>/
    給「帶領」逐步引導功能用：學生在任務清單頁把被引導的任務打勾完成後，
    前端呼叫這支 API 查詢有沒有對應的資訊中心指南可以附加成連結。
    """
    from flows.models import StudentTask

    student_task = StudentTask.objects.filter(
        id=student_task_id, student__user=request.user
    ).select_related('task').first()

    if not student_task:
        return Response({
            'success': False,
            'message': '找不到此任務',
            'data': None,
        }, status=status.HTTP_404_NOT_FOUND)

    guide = get_guide_page_for_task(student_task.task, request.user)

    return Response({
        'success': True,
        'data': guide,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def welcome_message_api(request):
    """
    POST /chatbot/api/welcome-message/
    給首次進 dashboard 的學生觸發歡迎訊息 + 帶到第一個任務。
    冪等（由 create_welcome_chat_messages 內的 has_received_welcome_chat 判斷），
    回應格式比照 GET /api/flows/reminders/ 的 proactive_chat，前端可直接複用同一套顯示邏輯。
    """
    session_id = create_welcome_chat_messages(request.user)
    return Response({
        'success': True,
        'data': {
            'has_new': bool(session_id),
            'session_id': session_id,
        },
    })

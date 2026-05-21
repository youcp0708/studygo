from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ChatSession, ChatMessage, ChatAttachment
from .services import generate_ai_reply
from django.utils import timezone
from django.utils.translation import gettext as _


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
            messages = active_session.messages.all()

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

    # 最多 3 則，超過就把剩餘合併進最後一則
    if len(parts) > 3:
        parts = parts[:2] + [''.join(parts[2:])]

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

    attachments = request.FILES.getlist('attachments')
    attachment_types = request.data.getlist('attachment_types')

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

    recent_messages = list(session.messages.order_by('-created_at')[:10])
    recent_messages.reverse()

    user_msg = ChatMessage.objects.create(
        session=session,
        role='user',
        content=message,
    )

    for index, uploaded_file in enumerate(attachments):
        attachment_type = 'file'

        if index < len(attachment_types):
            attachment_type = attachment_types[index]

        ChatAttachment.objects.create(
            message=user_msg,
            file=uploaded_file,
            attachment_type=attachment_type,
            original_name=uploaded_file.name,
        )

    ai_result = generate_ai_reply(
        user=request.user,
        question=message,
        recent_messages=recent_messages,
        ai_mode=ai_mode,
    )

    print("[DEBUG] ai_result source:", ai_result.get("source"))
    print("[DEBUG] ai_result model:", ai_result.get("model"))
    print("[DEBUG] ai_result reply:", ai_result.get("reply"))

    if ai_mode == "friend":
        reply_parts = split_friend_reply(ai_result['reply'])
    else:
        reply_parts = [ai_result['reply']]

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
        },
        # 新版：多則 AI 訊息
        'assistant_messages': assistant_messages,

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

"""
chatbot/views.py
AI 聊天機器人頁面與 API。
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ChatSession, ChatMessage
from .services import generate_ai_reply


@login_required(login_url='/login/')
@ensure_csrf_cookie
def chatbot_page(request):
    """前端聊天頁面。"""
    session = ChatSession.objects.filter(user=request.user).first()
    context = {
        'user': request.user,
        'profile': getattr(request.user, 'student_profile', None),
        'active_session': session,
    }
    return render(request, 'chatbot/chatbot.html', context)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_message_api(request):
    """
    POST /api/chatbot/message/
    Body: { "message": "簽證要準備什麼？", "session_id": 1 }
    """
    message = (request.data.get('message') or '').strip()
    session_id = request.data.get('session_id')

    if not message:
        return Response({
            'success': False,
            'message': '請輸入問題',
            'errors': {'message': 'message 不可為空'},
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(message) > 1200:
        return Response({
            'success': False,
            'message': '問題太長，請縮短到 1200 字以內',
            'errors': {'message': 'too_long'},
        }, status=status.HTTP_400_BAD_REQUEST)

    if session_id:
        session = ChatSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({
                'success': False,
                'message': '找不到此對話',
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        title = message[:24] + ('…' if len(message) > 24 else '')
        session = ChatSession.objects.create(user=request.user, title=title)

    recent_messages = list(session.messages.order_by('-created_at')[:10])
    recent_messages.reverse()

    user_msg = ChatMessage.objects.create(
        session=session,
        role='user',
        content=message,
    )

    ai_result = generate_ai_reply(
        user=request.user,
        question=message,
        recent_messages=recent_messages,
    )

    assistant_msg = ChatMessage.objects.create(
        session=session,
        role='assistant',
        content=ai_result['reply'],
    )

    # 第一次提問時，用問題作為標題；後續更新 updated_at
    session.save(update_fields=['updated_at'])

    return Response({
        'success': True,
        'message': 'AI 回覆成功',
        'data': {
            'session_id': session.id,
            'user_message': {
                'id': user_msg.id,
                'role': user_msg.role,
                'content': user_msg.content,
                'created_at': user_msg.created_at.strftime('%Y-%m-%d %H:%M'),
            },
            'assistant_message': {
                'id': assistant_msg.id,
                'role': assistant_msg.role,
                'content': assistant_msg.content,
                'created_at': assistant_msg.created_at.strftime('%Y-%m-%d %H:%M'),
            },
            'source': ai_result['source'],
            'model': ai_result['model'],
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history_api(request):
    """GET /api/chatbot/history/?session_id=1"""
    session_id = request.GET.get('session_id')
    session = None

    if session_id:
        session = ChatSession.objects.filter(id=session_id, user=request.user).first()
    else:
        session = ChatSession.objects.filter(user=request.user).first()

    if not session:
        return Response({
            'success': True,
            'message': '目前沒有聊天紀錄',
            'data': {
                'session_id': None,
                'messages': [],
            },
        })

    messages = [
        {
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        for msg in session.messages.all()
    ]

    return Response({
        'success': True,
        'message': '取得聊天紀錄成功',
        'data': {
            'session_id': session.id,
            'title': session.title,
            'messages': messages,
        },
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_history_api(request):
    """DELETE /api/chatbot/history/clear/"""
    ChatSession.objects.filter(user=request.user).delete()
    return Response({
        'success': True,
        'message': '聊天紀錄已清除',
        'data': {},
    })

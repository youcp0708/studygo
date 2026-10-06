"""
insights/classify.py
把尚未分類的學生提問寫入 QuestionClassification（規格 §8.3）。
"""

from django.conf import settings

from chatbot.models import ChatMessage

from .models import QuestionClassification
from .question_categories import MIN_LLM_LENGTH, classify_by_rules, classify_with_llm

LLM_BATCH_SIZE = 20


def pending_messages():
    """helper 模式中、學生本人發出、尚未分類的訊息。friend 模式一律不分析。"""
    return ChatMessage.objects.filter(
        role='user',
        session__ai_mode='helper',
        session__user__student_profile__isnull=False,
        insights_classification__isnull=True,
    ).order_by('id')


def llm_client():
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        return None
    from openai import OpenAI
    return OpenAI(api_key=api_key)


def classify_pending(limit=2000, use_llm=True, client=None):
    """
    回傳 {'rule': n, 'llm': n, 'none': n, 'llm_failed': n}。
    LLM 呼叫失敗的訊息不寫入結果，下次執行會再試一次。
    """
    stats = {'rule': 0, 'llm': 0, 'none': 0, 'llm_failed': 0}
    if use_llm and client is None:
        client = llm_client()
    use_llm = use_llm and client is not None
    model = getattr(settings, 'OPENAI_MODEL', None)

    results, llm_queue = [], []
    for message in pending_messages()[:limit]:
        category = classify_by_rules(message.content)
        if category:
            results.append(QuestionClassification(message=message, category=category, method='rule'))
        elif use_llm and len((message.content or '').strip()) >= MIN_LLM_LENGTH:
            llm_queue.append(message)
        else:
            results.append(QuestionClassification(message=message, category='other', method='none'))

    for i in range(0, len(llm_queue), LLM_BATCH_SIZE):
        batch = llm_queue[i:i + LLM_BATCH_SIZE]
        try:
            codes = classify_with_llm([m.content for m in batch], client, model)
        except Exception:
            stats['llm_failed'] += len(batch)
            continue
        for message, code in zip(batch, codes):
            if code:
                results.append(QuestionClassification(message=message, category=code, method='llm'))
            else:
                results.append(QuestionClassification(message=message, category='other', method='none'))

    QuestionClassification.objects.bulk_create(results, ignore_conflicts=True)
    for r in results:
        stats[r.method] += 1
    return stats

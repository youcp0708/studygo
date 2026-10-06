"""
insights/question_categories.py
學生向 AI 小幫手提問的分類。

分類代碼與 task_categories 對齊（entry_permit、residence_permit…），
這樣才能做「提問率高 + 逾期率高」的交叉分析。

流程：先用關鍵字規則，規則沒命中才交給 LLM（見 classify_with_llm）。
原文只在這裡處理，不會寫進任何分析表。
"""

import json
import re

from chatbot.services import keyword_matches

QUESTION_CATEGORY_CHOICES = [
    ('entry_permit', '簽證／入出境許可'),
    ('residence_permit', '居留證件'),
    ('nhi', '全民健保'),
    ('housing', '住宿'),
    ('registration', '報到註冊'),
    ('health_check', '健康檢查'),
    ('course', '選課'),
    ('bank', '銀行開戶'),
    ('work_permit', '工作許可'),
    ('scholarship', '獎助學金'),
    ('medical', '就醫'),
    ('daily_life', '生活（交通、手機、飲食）'),
    ('other', '其他'),
]
QUESTION_CATEGORY_LABELS = dict(QUESTION_CATEGORY_CHOICES)
QUESTION_CATEGORY_CODES = [code for code, _ in QUESTION_CATEGORY_CHOICES]

# 依序比對，先命中先贏（排序理由同 task_categories.KEYWORD_RULES）
KEYWORD_RULES = [
    ('work_permit', ['work permit', 'part-time', 'part time', '工作許可', '工作證', '打工', '兼職', '工讀']),
    ('entry_permit', ['visa', '簽證']),
    ('residence_permit', ['arc', 'residence permit', 'resident certificate', '居留']),
    ('entry_permit', ['entry permit', '入出境許可', '入境許可']),
    ('health_check', ['health check', 'health exam', 'medical exam', 'physical exam', '健康檢查', '健檢', '體檢']),
    ('nhi', ['nhi', 'health insurance', '健保', '健康保險']),
    ('housing', ['housing', 'dorm', 'dormitory', 'rent', 'renting', '宿舍', '住宿', '租屋', '房租']),
    ('course', ['course', 'courses', 'class', 'classes', '選課', '加退選', '課程', '修課']),
    ('registration', ['registration', 'register', 'check-in', 'enrollment', 'tuition', '報到', '註冊', '學費']),
    ('bank', ['bank', 'bank account', '銀行', '開戶']),
    ('scholarship', ['scholarship', 'scholarships', '獎學金', '助學金']),
    ('medical', ['hospital', 'clinic', 'doctor', 'medical', '醫院', '診所', '看病', '就醫']),
    ('daily_life', ['bus', 'mrt', 'train', 'sim card', 'phone number', 'food', '公車', '捷運', '火車', '手機', '門號', '電話卡', '餐廳', '美食']),
]

# 少於這麼多字的訊息（例如「hi」「謝謝」）直接歸 other，不浪費 LLM 呼叫
MIN_LLM_LENGTH = 4


def classify_by_rules(text):
    """關鍵字規則分類。沒命中回傳 None。"""
    lower = (text or '').lower()
    for category, keywords in KEYWORD_RULES:
        if any(keyword_matches(k, lower) for k in keywords):
            return category
    return None


# ── 送 LLM 前遮蔽個資 ──
_EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
# 證件號碼：字母開頭的英數混合（例如護照 A12345678、居留證 A800000014）
_ID_RE = re.compile(r'\b[A-Za-z]{1,2}\d{6,9}\b')
# 電話、帳號等長數字（允許中間有空白或連字號）
_LONG_DIGITS_RE = re.compile(r'\+?\d[\d\s-]{6,}\d')


def mask_pii(text):
    text = _EMAIL_RE.sub('[EMAIL]', text or '')
    text = _ID_RE.sub('[ID]', text)
    text = _LONG_DIGITS_RE.sub('[NUMBER]', text)
    return text


def classify_with_llm(texts, client, model):
    """
    一次分類多則提問。回傳與 texts 等長的分類代碼 list；
    LLM 回傳格式不對或代碼不在清單內時，該則回傳 None（由呼叫端歸為 other）。
    """
    category_lines = '\n'.join(f'- {code}: {label}' for code, label in QUESTION_CATEGORY_CHOICES)
    numbered = '\n'.join(f'{i}. {mask_pii(t)[:500]}' for i, t in enumerate(texts))
    instructions = (
        '你是分類器。以下是在台境外學生向行政小幫手提出的問題（可能是任何語言）。'
        '請把每一則歸到下列其中一個分類代碼：\n'
        f'{category_lines}\n'
        '只輸出 JSON 陣列，依序列出每一則的分類代碼，例如 ["nhi","other"]，不要輸出其他文字。'
    )
    response = client.responses.create(model=model, instructions=instructions, input=numbered)
    raw = (response.output_text or '').strip()
    match = re.search(r'\[.*\]', raw, re.S)
    try:
        codes = json.loads(match.group(0)) if match else []
    except json.JSONDecodeError:
        codes = []
    if not isinstance(codes, list) or len(codes) != len(texts):
        return [None] * len(texts)
    return [c if c in QUESTION_CATEGORY_CODES else None for c in codes]

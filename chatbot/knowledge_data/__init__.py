"""
chatbot/knowledge_data/

知識庫內容的資料來源，依主題分成多個模組，每個模組匯出一個 ENTRIES list。

每筆資料的欄位：
    category       必填，對應 ChatKnowledge.CATEGORY_CHOICES
    title          必填，繁體中文標題（同時作為自然鍵的一部分）
    content        必填，繁體中文內容
    keywords       建議填，中英文皆放，提高 RAG 命中率
    source_url     官方出處，會附在 AI 回答後供學生查證
    university     留空＝所有學校通用；各校做法不同的內容要指定
    country        留空＝所有國籍通用；各國做法不同的內容要指定
    identity_type  留空＝僑生／外籍生／港澳生皆適用
    bot_type       預設 helper，生活陪伴類可設 both
    verified_at    已對照官網查核的日期（datetime.date）；留空代表尚未查核

新增主題時：建立 <name>.py，定義 ENTRIES，再把檔名加進 MODULE_ORDER。
"""

import importlib

# 載入順序（也決定 --only 可用的名稱）
MODULE_ORDER = [
    'general_documents',
    'visa',
    'schools',
    'admission',
    'life',
    'ncu',
]


def iter_modules(only=''):
    """依序 yield (模組名稱, ENTRIES)。only 有值時只回傳該模組。"""
    names = [only] if only else MODULE_ORDER

    for name in names:
        if name not in MODULE_ORDER:
            raise ValueError(f'未知的知識庫模組：{name}；可用：{", ".join(MODULE_ORDER)}')
        module = importlib.import_module(f'{__name__}.{name}')
        yield name, getattr(module, 'ENTRIES', [])

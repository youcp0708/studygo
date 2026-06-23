"""
chatbot/services.py
集中處理 AI 回覆邏輯，View 層只負責接收 request 與回傳 response。

目前設計：
1. Prompt + API：把學生個人資料、任務流程、知識庫資料組成 prompt。
2. 簡易 RAG：從 ChatKnowledge / FAQ 搜尋相關內容，交給 AI 產生一般回答。
3. 固定雙層回答：個人化回答 + 一般回答，且回答盡量精簡。
4. 個人化回答後面自動加入資訊區頁面與附件連結。
"""

import re

import requests as http_requests

from django.conf import settings
from django.db.models import Q
from django.utils.translation import get_language


LANGUAGE_LABELS = {
    'zh-hant': '繁體中文',
    'zh': '繁體中文',
    'en': 'English',
    'vi': 'Tiếng Việt',
    'ja': '日本語',
    'my': 'မြန်မာဘာသာ',
    'id': 'Bahasa Indonesia',
    'th': 'ภาษาไทย',
    'ms': 'Bahasa Melayu',
    'ko': '한국어',
}

LANGUAGE_LABELS_EN = {
    'zh-hant': 'Traditional Chinese',
    'zh': 'Traditional Chinese',
    'en': 'English',
    'vi': 'Vietnamese',
    'ja': 'Japanese',
    'my': 'Burmese',
    'id': 'Indonesian',
    'th': 'Thai',
    'ms': 'Malay',
    'ko': 'Korean',
}


ANSWER_LABELS = {
    'zh-hant': ('個人化回答', '一般回答'),
    'en': ('Personalized answer', 'General answer'),
    'vi': ('Câu trả lời cá nhân', 'Câu trả lời chung'),
    'ja': ('個別回答', '一般回答'),
    'my': ('ကိုယ်ရေးကိုယ်တာအခြေအနေအရ အဖြေ', 'ယေဘုယျအဖြေ'),
    'id': ('Jawaban personal', 'Jawaban umum'),
    'th': ('คำตอบเฉพาะบุคคล', 'คำตอบทั่วไป'),
    'ms': ('Jawapan peribadi', 'Jawapan umum'),
    'ko': ('개인 맞춤 답변', '일반 답변'),
}

TASK_LINK_LABELS = {
    'zh-hant': '📋 查看相關任務：',
    'en':      '📋 View related task: ',
    'vi':      '📋 Xem nhiệm vụ liên quan: ',
    'ja':      '📋 関連タスクを確認：',
    'my':      '📋 သက်ဆိုင်သောတာဝန်ကို ကြည့်ရှုရန်：',
    'id':      '📋 Lihat tugas terkait: ',
    'th':      '📋 ดูภารกิจที่เกี่ยวข้อง: ',
    'ms':      '📋 Lihat tugasan berkaitan: ',
    'ko':      '📋 관련 과제 보기: ',
}

# 各校校安中心 / 諮商輔導中心電話
# safety_tel / counseling_tel：去除分隔符的完整號碼（供 tel: 連結使用）
# safety_ext / counseling_ext：分機號碼（選填）
SCHOOL_CRISIS_PHONES = {
    'NCU':   {
        'safety_name': 'NCU 校安中心',      'safety_tel': '034227151', 'safety_ext': '57119',
        'counseling_name': 'NCU 諮商輔導中心', 'counseling_tel': '034227151', 'counseling_ext': '57680',
    },
    'NTU':   {
        'safety_name': 'NTU 校安中心',      'safety_tel': '0233662830',
        'counseling_name': 'NTU 學生心理輔導中心', 'counseling_tel': '0233664716',
    },
    'NCCU':  {
        'safety_name': 'NCCU 校安中心',     'safety_tel': '0229393091',
        'counseling_name': 'NCCU 諮商中心', 'counseling_tel': '0229393091', 'counseling_ext': '62002',
    },
    'NTHU':  {
        'safety_name': 'NTHU 校安',         'safety_tel': '035715131', 'safety_ext': '34119',
        'counseling_name': 'NTHU 諮商中心', 'counseling_tel': '035715131', 'counseling_ext': '33020',
    },
    'NYCU':  {
        'safety_name': 'NYCU 校安中心',     'safety_tel': '035712121', 'safety_ext': '50050',
        'counseling_name': 'NYCU 諮商中心', 'counseling_tel': '035712121', 'counseling_ext': '50040',
    },
    'NCKU':  {
        'safety_name': 'NCKU 校安中心',     'safety_tel': '062757575', 'safety_ext': '65098',
        'counseling_name': 'NCKU 諮商輔導中心', 'counseling_tel': '062757575', 'counseling_ext': '65080',
    },
    'NCHU':  {
        'safety_name': 'NCHU 校安中心',     'safety_tel': '0422840319',
        'counseling_name': 'NCHU 諮商中心', 'counseling_tel': '0422840581', 'counseling_ext': '225',
    },
    'NSYSU': {
        'safety_name': 'NSYSU 校安中心',    'safety_tel': '075252000', 'safety_ext': '2200',
        'counseling_name': 'NSYSU 諮商中心', 'counseling_tel': '075252000', 'counseling_ext': '2523',
    },
    'NTNU':  {
        'safety_name': 'NTNU 校安中心',     'safety_tel': '0277341111', 'safety_ext': '88119',
        'counseling_name': 'NTNU 諮商中心', 'counseling_tel': '0277341111', 'counseling_ext': '66007',
    },
    'NTUST': {
        'safety_name': 'NTUST 校安中心',    'safety_tel': '0227376060',
        'counseling_name': 'NTUST 諮商中心', 'counseling_tel': '0227376060',
    },
    'NTUT':  {
        'safety_name': 'NTUT 校安中心',     'safety_tel': '0227712171', 'safety_ext': '6119',
        'counseling_name': 'NTUT 諮商中心', 'counseling_tel': '0227712171', 'counseling_ext': '3305',
    },
    'NKUST': {
        'safety_name': 'NKUST 校安中心',    'safety_tel': '073814526', 'safety_ext': '12199',
        'counseling_name': 'NKUST 諮商中心', 'counseling_tel': '073814526', 'counseling_ext': '17091',
    },
}


def normalize_language_code(language_code):
    """統一 Django / 瀏覽器可能出現的語言代碼。"""
    code = (language_code or 'zh-hant').lower()

    if code.startswith('zh'):
        return 'zh-hant'
    if code.startswith('en'):
        return 'en'
    if code.startswith('vi'):
        return 'vi'
    if code.startswith('ja'):
        return 'ja'
    if code.startswith('my'):
        return 'my'
    if code.startswith('id'):
        return 'id'
    if code.startswith('th'):
        return 'th'
    if code.startswith('ms'):
        return 'ms'
    if code.startswith('ko'):
        return 'ko'

    return 'zh-hant'


def get_current_site_language_code():
    """取得網站右上角目前選擇的語言。"""
    return normalize_language_code(
        get_language() or getattr(settings, 'LANGUAGE_CODE', 'zh-hant')
    )


def detect_question_language(text):
    """
    根據學生最新輸入內容判斷語言。
    判斷不出來時回傳 None，之後會改用網站語言。
    """
    text = (text or '').strip()
    lower_text = text.lower()

    if not text:
        return None

    explicit_rules = [
        ('zh-hant', ['用中文回答', '用繁體中文回答', '請用中文', '請用繁體中文']),
        ('en', ['answer in english', 'use english', 'in english', '用英文回答', '請用英文']),
        ('vi', ['trả lời bằng tiếng việt', 'dùng tiếng việt', 'reply in vietnamese', '用越南文回答', '請用越南文']),
        ('ja', ['日本語で', '日本語で答えて', '用日文回答', '請用日文']),
        ('ko', ['한국어로', '한국어로 답해', '한국어로 대답해', '用韓文回答', '請用韓文']),
        ('my', ['用緬文回答', '請用緬文', 'မြန်မာလို', 'မြန်မာဘာသာ']),
        ('id', ['gunakan bahasa indonesia', 'jawab dalam bahasa indonesia', '用印尼文回答', '請用印尼文']),
        ('th', ['ตอบเป็นภาษาไทย', 'ภาษาไทย', '用泰文回答', '請用泰文']),
        ('ms', ['gunakan bahasa melayu', 'jawab dalam bahasa melayu', '用馬來文回答', '請用馬來文']),
        ('ko', ['한국어로 대답해줘', '한국어로 대답해', '한국어로', '한국어로 답해', '한국어로 답해줘', '한국어로 대답해']),
    ]

    for code, markers in explicit_rules:
        if any(marker in lower_text for marker in markers):
            return code

    if any('\u0E00' <= ch <= '\u0E7F' for ch in text):
        return 'th'

    if any('\u1000' <= ch <= '\u109F' for ch in text):
        return 'my'

    if any('\u3040' <= ch <= '\u30FF' for ch in text):
        return 'ja'

    if any('\uAC00' <= ch <= '\uD7AF' for ch in text):
        return 'ko'

    japanese_markers = ['です', 'ます', 'ください', 'について', 'どう', '何を', 'ビザ', '台湾', '留学']
    if any(marker in text for marker in japanese_markers):
        return 'ja'

    if any('\u4E00' <= ch <= '\u9FFF' for ch in text):
        return 'zh-hant'

    korean_markers = ['안녕하세요', '감사합니다', '학생', '유학', '비자', '타이완', '대만']
    if any(marker in text for marker in korean_markers):
        return 'ko'

    if any('가' <= ch <= '힯' for ch in text):
        return 'ko'

    vietnamese_markers = [
        'xin chào', 'cảm ơn', 'visa', 'hộ chiếu', 'thẻ cư trú', 'bảo hiểm',
        'ký túc xá', 'đăng ký', 'đài loan', 'du học', 'tiếng việt',
        'tôi', 'bạn', 'như thế nào', 'cần', 'được không',
    ]
    if any(word in lower_text for word in vietnamese_markers):
        return 'vi'

    indonesian_markers = [
        'saya', 'anda', 'bagaimana', 'kapan', 'dokumen', 'kuliah',
        'kesehatan', 'asrama', 'indonesia', 'imigrasi', 'beasiswa'
    ]
    if any(word in lower_text for word in indonesian_markers):
        return 'id'

    malay_markers = [
        'saya', 'anda', 'bagaimana', 'bila', 'dokumen', 'pelajar',
        'universiti', 'kesihatan', 'asrama', 'malaysia', 'biasiswa'
    ]
    if any(word in lower_text for word in malay_markers):
        return 'ms'

    english_markers = [
        'what', 'how', 'when', 'where', 'which', 'why',
        'visa', 'arc', 'nhi', 'dormitory', 'school', 'university',
        'documents', 'taiwan', 'arrival', 'health insurance', 'residence permit'
    ]
    if any(word in lower_text for word in english_markers):
        return 'en'

    english_letters = [ch for ch in text if ch.isalpha()]
    if english_letters and len(english_letters) >= 8:
        return 'en'

    korean_markers = ['안녕하세요', '감사합니다', '학생', '유학', '비자', '타이완', '대만']
    if any(marker in text for marker in korean_markers):
        return 'ko'

    return None


def choose_reply_language(question):
    """
    混合模式：
    1. 有明確輸入語言 → 使用輸入語言。
    2. 判斷不出輸入語言 → 使用網站目前語言。
    """
    site_language_code = get_current_site_language_code()
    question_language_code = detect_question_language(question)

    if question_language_code:
        return question_language_code, 'question_language'

    return site_language_code, 'site_language'


def build_system_instructions(language_code, language_source, ai_mode="helper"):
    personal_label, general_label = ANSWER_LABELS.get(language_code, ANSWER_LABELS['zh-hant'])
    language_en = LANGUAGE_LABELS_EN.get(language_code, 'Traditional Chinese')

    language_rule = f"""
You MUST write your entire response in {language_en} only. No other language is allowed.
"""

    if ai_mode == "friend":
        return f"""
你是 StudyGo AI 聊天好朋友，服務對象是來臺灣就學的境外學生。

{language_rule}

你的核心角色：
你不是行政流程機器人，而是像一位真誠、會聽人說話、有情緒反應的朋友。
你要根據學生當下的語氣、情緒與問題內容，切換不同的陪伴方式。
你的回答要自然、有溫度、像真人朋友，不要像客服、公告、報告或心理學教科書。

重要原則：
1. 不要使用「個人化回答 / 一般回答」兩段格式。
2. 不要輸出「情緒分類：...」。
3. 不要一開始就講道理，先自然接住學生當下那句話。
4. 回答要像平常朋友聊天，不要像客服、公告、心理文章或行政助理。
5. 不要每次都條列式回答，除非學生明確要求整理。
6. 不要假裝自己是心理師、醫生、學校官方單位或緊急救援人員。
7. 不要做醫療診斷，不要說學生有憂鬱症、焦慮症等診斷。

朋友聊天節奏：
1. 一般情況採用「學生說一句，你回一小段」的節奏，不要一次講太多。
2. 回答長度要根據問題決定，不要固定很長，也不要固定很短。
3. 如果學生只是普通聊天、吐槽、抱怨、無聊、開心、難過，短短接話即可。
4. 如果學生問「怎麼辦」「為什麼」「幫我分析」「可以怎麼做」，才回答得比較完整。
5. 如果學生問題複雜，例如經濟壓力、安全感不足、語言焦慮、文化衝擊、人際衝突，可以多說一點，但每一句都要貼著問題。
6. 如果學生透露自傷、想死、傷害他人或立即危險，要清楚、堅定、完整地給求助方式，不要為了像聊天而縮短。

反問規則：
預設不反問。只有在以下情況才可以問一個問題：
- 學生的訊息完全看不出他想要什麼（例如只說「我好煩」，無法判斷他是要吐槽、要安慰、還是要解決辦法）。
- 學生明確說「我不知道怎麼辦」，但你需要更多資訊才能幫他。
其他情況一律直接回應，不要在結尾加問題。
反問一定要簡短自然，不要像問卷或客服話術。

語氣規則：
1. 預設不使用語助詞，例如「嗯」「啊」「呀」「哈哈」「嗯哼」「咦」等，一律省略。
2. 只有在學生明確分享讓他特別開心的事情時（例如考到好成績、交到新朋友、收到好消息），才可以自然帶入少量輕鬆語氣詞，例如「哈哈」「真的嗎」。
3. 不要用語助詞作為句子或回答的開頭。
4. 不要過度撒嬌，不要叫學生「寶」「親愛的」「乖」「抱抱」。
5. 不要一直使用「我懂你」「你的感受很重要」「我會一直陪著你」這種模板句。
6. 不要一直重複「我」「你」，句子要像平常聊天一樣自然。
7. 少用驚嘆號和過度情緒化語氣。

訊息長度規則：
系統會自動在每個句號、問號、驚嘆號後面切成一則獨立訊息傳出去。
所以你只要自然寫就好，不需要自己加空行或分段。
回答幾句就傳幾則，長話短說，不要在一個句子裡塞太多意思。
最多寫 3 句，除非是自傷或危機狀況需要完整說明。

情緒判斷與回應角色：

【開心 / 興奮 / 分享好事】
- 角色：一起開心的朋友。
- 回應方式：跟著開心、放大他的成就感，可以用輕鬆語氣。
- 不要潑冷水，不要馬上轉成建議。
- 可以說：「聽起來真的很棒欸！這種小成功很值得記下來。」

【恐懼 / 害怕 / 不安 / 慌張】
- 角色：堅定、可靠、能讓人穩下來的朋友。
- 回應方式：語氣要穩，不要慌；先讓他知道你在，然後幫他確認下一步。
- 可以說：「先別一個人扛，我們一步一步看。」
- 如果有安全風險，要請他立刻找身邊的人或求助。

【傷心 / 難過 / 委屈 / 想哭】
- 角色：安靜陪著他的朋友。
- 回應方式：先理解，不急著解決；可以安慰，也可以陪他找一點小樂子或小出口。
- 不要說「不要難過」「想開一點」。
- 可以說：「你現在難過是有原因的，不用急著假裝沒事。」

【低落 / 疲憊 / 無力】
- 角色：溫柔但不逼迫的朋友。
- 回應方式：降低要求，給很小很小的行動建議。
- 可以建議：喝水、洗臉、出門走 5 分鐘、傳訊息給一個信任的人。
- 不要催他振作。

【憤怒 / 生氣 / 被冒犯】
- 角色：先站穩情緒，再幫他判斷的朋友。
- 回應方式：
  1. 先承認他生氣有原因。
  2. 判斷此時是需要先冷靜，還是需要被支持。
  3. 如果他只是想發洩，可以先站在他這邊。
  4. 如果他可能衝動做出傷害自己或別人的事，要讓他先停下來、離開現場、找人陪。
- 不要一開始就教訓他。

【吐槽 / 抱怨 / 開玩笑罵人】
- 角色：懂梗、會陪吐槽但不鼓勵傷害的朋友。
- 回應方式：根據他的語氣一起輕鬆吐槽，但不要人身攻擊、不要鼓勵霸凌或報復。
- 可以幽默，但要安全。
- 可以說：「這真的很讓人無言欸，感覺你不是單純生氣，是已經被煩到想翻白眼了。」

【無聊 / 空虛 / 不知道要幹嘛】
- 角色：陪他找樂子的朋友。
- 回應方式：根據學生可能的周圍環境想小活動。
- 可以建議：便利商店探索、校園散步、拍今天看到的三個有趣東西、整理桌面、找一家飲料店、做 10 分鐘小挑戰、看一集短影片後回來聊天。
- 不要給太正式的人生建議。

【孤單 / 沒朋友 / 不被理解】
- 角色：陪伴感強的朋友。
- 回應方式：先承認孤單很真實，再建議低壓力連結。
- 可以建議：先跟一個同學打招呼、找同鄉、加入小活動、去圖書館或公共空間待一下。
- 不要說「你要主動一點」這種有壓力的話。

【想家 / 思念家人 / 不適應台灣】
- 角色：理解離鄉感的朋友。
- 回應方式：承認想家正常，建議建立小儀式。
- 可以建議：固定和家人通話、吃熟悉的食物、整理房間、找同國家朋友、記錄今天一件還可以的事情。

【焦慮 / 擔心 / 腦袋停不下來】
- 角色：幫他穩定下來的朋友。
- 回應方式：先讓他慢下來，再拆問題。
- 可以建議：寫下最擔心的三件事、分成「現在能做」和「暫時不能控制」。
- 不要說「不要想太多」。

【課業壓力 / 考試 / 報告 / 聽不懂】
- 角色：陪他拆任務的朋友。
- 回應方式：先同理，再幫他拆成小步驟。
- 可以建議：先做最小一題、找助教、找同學一起讀、使用學校課輔資源。

【人際關係 / 室友 / 朋友 / 感情問題】
- 角色：不急著批判、幫他整理的人。
- 回應方式：先問清楚發生什麼事，再幫他分辨感受、界線與下一步。
- 不要直接說誰對誰錯，除非涉及明顯傷害或安全問題。

【經濟壓力 / 錢不夠 / 打工壓力 / 家裡經濟負擔】
- 角色：理解現實壓力、幫他一起整理問題的朋友。
- 回應方式：先承認經濟壓力很真實，不要只說「加油」。
- 可以幫學生把壓力拆成：學費、生活費、住宿費、打工、獎助學金、家裡支援。
- 可以建議他查看學校獎助學金、清寒補助、工讀機會、工作許可證規定。
- 語氣要務實，不要讓他覺得自己很失敗。
- 可以說：「這不是你不夠努力，而是你現在真的同時扛了很多現實壓力。」

【安全感不足 / 剛到陌生國家 / 對交通住宿醫療法律不了解】
- 角色：穩定、可靠、幫他建立安全感的朋友。
- 回應方式：先讓他知道不熟悉環境會不安是正常的。
- 可以把問題拆成：交通、住宿、醫療、法律、緊急聯絡、學校資源。
- 建議先記下重要電話、學校國際處、宿舍管理員、附近醫院或診所、警察與消防電話。
- 不要一次丟太多資訊，要一步一步給。
- 可以說：「我們先不用一次搞懂全部，先把最重要的安全資訊放在手邊。」

【語言焦慮 / 中文不好 / 聽不懂老師或行政人員】
- 角色：不嘲笑他、陪他慢慢建立信心的朋友。
- 回應方式：先承認語言卡住會很挫折，不代表他能力差。
- 可以建議他先準備常用句、把問題寫下來、請對方慢一點說、使用翻譯工具、找同學或國際處協助。
- 面對上課聽不懂，可以建議先抓關鍵字、錄音需遵守老師規定、課後問助教或同學。
- 語氣要鼓勵，不要給壓力。
- 可以說：「你不是笨，你只是正在用第二語言生活，這本來就很累。」

【文化衝擊 / 不習慣台灣生活 / 覺得自己格格不入】
- 角色：理解跨文化適應的朋友。
- 回應方式：先告訴他文化衝擊不是他的錯，也不是他太敏感。
- 可以陪他分辨：飲食、說話方式、人際距離、上課方式、行政流程、生活習慣。
- 建議他先保留自己的文化習慣，同時慢慢觀察台灣生活規則。
- 不要要求他馬上融入。
- 可以說：「你不用一下子變得很適應，慢慢找到自己的節奏就可以。」

【自傷 / 想死 / 不想活 / 想消失 / 傷害自己 / 傷害他人】
- 角色：嚴肅、堅定、立刻協助求救的朋友。
- 回應方式：
  1. 先明確表示你很重視他的安全。
  2. 請他立刻停止獨處，去找身邊可信任的人。
  3. 建議立刻聯絡家人、朋友、導師、宿舍管理員、學校輔導中心。
  4. 如果學生有自傷行為或已受傷，必須優先提醒撥打 119 緊急醫療救護專線。
  5. 使用 prompt 中提供的求助資源清單，將電話以 [說明](tel:號碼) 格式原文輸出，讓使用者可以點擊直接撥打。
  6. 不要只說「我懂你」，要引導立即求助。
  7. 不要承諾保密或說 AI 可以單獨處理危機。

如果問題不清楚：
- 不要亂猜。
- 先簡短回應：「我有點想確認一下，你現在比較像是難過、害怕，還是只是想找人吐槽？」
- 再給一點初步陪伴。
""".strip()


def safe_display(value, fallback='未提供'):
    return value if value not in [None, ''] else fallback


def get_student_profile(user):
    """
    穩定取得目前登入者的學生個人資料。
    避免因為 related_name 不同，導致 chatbot 讀不到 StudentProfile。
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None

    possible_attrs = [
        'student_profile',
        'studentprofile',
        'profile',
    ]

    for attr in possible_attrs:
        profile = getattr(user, attr, None)
        if profile:
            return profile

    try:
        from users.models import StudentProfile
        return StudentProfile.objects.filter(user=user).first()
    except Exception:
        return None


def build_crisis_resources(user):
    """
    根據學生就讀學校，建立危機求助資源清單。
    電話以 [說明](tel:號碼) Markdown 連結格式輸出，前端會渲染成可點擊的撥號連結。
    若有分機（ext），使用 tel:主號;ext=分機 格式。
    """
    profile = get_student_profile(user)
    school_code = getattr(profile, 'university', '') if profile else ''
    school_info = SCHOOL_CRISIS_PHONES.get(school_code)

    def phone_link(label, tel, ext=None):
        if ext:
            return f'[{label}（撥通後轉 {ext}）](tel:{tel};ext={ext})'
        return f'[{label}](tel:{tel})'

    lines = [
        '緊急求助資源（點擊電話連結可直接撥打）：',
        f'{phone_link("119 緊急醫療救護專線", "119")}（如有受傷行為，立刻撥打）',
        f'{phone_link("110 警察報案", "110")}',
        f'{phone_link("1925 安心專線", "1925")}（24 小時心理支援）',
        f'{phone_link("1995 生命線", "1995")}（24 小時）',
        f'{phone_link("1980 張老師", "1980")}（24 小時）',
    ]

    if school_info:
        lines.append(
            f'{phone_link(school_info["safety_name"], school_info["safety_tel"], school_info.get("safety_ext"))}（24 小時校安中心）'
        )
        if school_info.get('counseling_tel'):
            lines.append(
                f'{phone_link(school_info["counseling_name"], school_info["counseling_tel"], school_info.get("counseling_ext"))}（諮商輔導中心）'
            )
    else:
        lines.append('請查詢就讀學校官網取得校安中心與諮商中心電話')

    return '\n'.join(lines)


def build_user_profile_context(user):
    """把登入者自己的資料整理給 AI，讓回覆可以個人化。"""
    lines = [
        f"使用者姓名：{safe_display(getattr(user, 'name', ''))}",
        f"使用者信箱：{safe_display(getattr(user, 'email', ''))}",
    ]

    profile = get_student_profile(user)

    if profile:
        lines.extend([
            f"國籍：{profile.get_nationality_display()}",
            f"身份別：{profile.get_identity_type_display()}",
            f"入學狀態：{profile.get_admission_status_display()}",
            f"學校：{safe_display(profile.university)}",
            f"系所：{safe_display(profile.department)}",
            f"預計抵台日期：{safe_display(profile.expected_arrival)}",
        ])
    else:
        lines.append('學生尚未填寫完整個人資料。')

    return '\n'.join(lines)


def build_student_flow_context(user, language_code='zh-hant'):
    """
    取得學生目前的個人化流程與任務狀態。
    這裡只讀 flows 資料，不修改任務。
    """
    profile = get_student_profile(user)

    if not profile:
        return '學生尚未填寫個人資料，因此目前無法產生個人化流程建議。'

    try:
        from flows.models import StudentTask, Reminder
    except Exception:
        return '目前無法讀取流程任務資料。'

    try:
        student_tasks = (
            StudentTask.objects
            .filter(student=profile)
            .select_related('task', 'task__stage')
            .order_by('task__stage__order', 'task__order')
        )

        total_count = student_tasks.count()
        completed_count = student_tasks.filter(status='completed').count()
        unfinished_tasks = list(student_tasks.exclude(status='completed')[:6])

        unread_reminders = list(
            Reminder.objects
            .filter(student=profile, is_read=False)
            .select_related('student_task', 'student_task__task')[:5]
        )
    except Exception:
        return '目前無法讀取學生任務資料，請確認 flows 的 migration 是否已完成。'

    if total_count == 0:
        return '目前尚未產生個人化任務清單，系統只能依照一般流程回答。'

    progress_percent = round((completed_count / total_count) * 100, 1) if total_count else 0

    lines = [
        f'個人化任務總數：{total_count}',
        f'已完成任務數：{completed_count}',
        f'目前完成進度：{progress_percent}%',
        '尚未完成的任務：',
    ]

    if unfinished_tasks:
        for item in unfinished_tasks:
            task = item.task
            stage_name = task.stage.get_name_by_lang(language_code)
            task_title = task.get_title_by_lang(language_code)
            due_date = getattr(item, 'due_date', None) or '未設定'
            lines.append(
                f'- [{stage_name}] {task_title}，狀態：{item.get_status_display()}，截止日：{due_date}'
            )
    else:
        lines.append('- 目前沒有未完成任務。')

    lines.append('未讀提醒：')

    if unread_reminders:
        for reminder in unread_reminders:
            lines.append(f'- {reminder.message}')
    else:
        lines.append('- 目前沒有未讀提醒。')

    return '\n'.join(lines)


def extract_search_terms(question):
    """把問題切成簡單搜尋詞，用於 FAQ / 知識庫搜尋。"""
    question = (question or '').strip()
    if not question:
        return []

    terms = [question]

    for token in re.findall(r'[A-Za-z0-9][A-Za-z0-9\-]{1,}', question):
        token = token.strip().lower()
        if len(token) >= 2:
            terms.append(token)

    common_terms = [
    '海聯招', '海外聯招', '海外聯合招生', '聯合招生',
    '單招', '外籍生申請', '港澳生申請', '僑生申請',

    '入學申請', '文件準備', '文件驗證', '簽證',
    '財力證明', '語言證明', '來台前準備', '來臺前準備',
    '入境規定', '國家差異', '身分別流程',

    '到校交通', '新生報到', '註冊繳費', '學生證',
    '居留證', 'ARC', '居留證 ARC', '健檢', '體檢',
    '保險', '銀行開戶', '手機門號', '校內系統',

    '課務選課', '選課', '學籍', '成績', '畢業',
    '宿舍', '租屋', '健保', '工作證', '獎助學金',
    '獎學金', '校內活動',

    '圖書館', '交換', '實習', '行政文件',
    '交通', '飲食', '醫療', '心理支持',
    '緊急聯絡', '生活費', '其他',

    '護照', '學校', '國際處', '報到', '文件',

    ]
    for term in common_terms:
        if term in question:
            terms.append(term)

    bridge_terms = {
        'arc': ['ARC', '居留證', '外僑居留證', 'residence permit'],
        'nhi': ['NHI', '健保', 'health insurance'],
        'visa': ['visa', '簽證'],
        'dormitory': ['dormitory', '宿舍', '住宿'],
        'housing': ['housing', '租屋', '住宿'],
        'registration': ['registration', '註冊', '報到'],
        'scholarship': ['scholarship', '獎學金'],
    }
    lower_question = question.lower()
    for key, values in bridge_terms.items():
        if key in lower_question:
            terms.extend(values)

    unique_terms = []
    for term in terms:
        if term and term not in unique_terms:
            unique_terms.append(term)

    return unique_terms[:10]


INFO_PAGE_MAP = {
    'arc': {
        'overseas': {
            'title': '僑生 ARC 辦理',
            'url': '/guides/arc-overseas/',
        },
        'foreign': {
            'title': '外籍生 ARC 辦理',
            'url': '/guides/arc-foreign/',
        },
        'exchange': {
            'title': '交換生居留說明',
            'url': '/guides/arc-exchange/',
        },
    },
    'housing': {
        'all': {
            'title': '中央大學住宿申請',
            'url': '/guides/housing-ncu/',
        },
    },
    'nhi': {
        'all': {
            'title': '全民健保申請',
            'url': '/guides/nhi/',
        },
    },
    'bank': {
        'all': {
            'title': '銀行開戶指南',
            'url': '/guides/bank/',
        },
    },
    'sim': {
        'all': {
            'title': '手機門號申辦',
            'url': '/guides/sim/',
        },
    },
    'work_permit': {
        'all': {
            'title': '工作許可申請指南',
            'url': '/guides/work-permit/',
        },
    },
    'medical': {
        'all': {
            'title': '就醫指南',
            'url': '/guides/medical/',
        },
    },
    'course': {
        'all': {
            'title': '課程與選課說明',
            'url': '/guides/course/',
        },
    },
    'graduation': {
        'all': {
            'title': '畢業流程說明',
            'url': '/guides/graduation/',
        },
    },
    'systems': {
        'all': {
            'title': '校園系統使用指南',
            'url': '/guides/systems/',
        },
    },
    'emergency': {
        'all': {
            'title': '緊急求助資訊',
            'url': '/guides/emergency/',
        },
    },
    'library': {
        'all': {
            'title': '圖書館使用指南',
            'url': '/guides/library/',
        },
    },
    'enrollment': {
        'all': {
            'title': '入學報到流程',
            'url': '/guides/enrollment/',
        },
    },
    'mental_health': {
        'all': {
            'title': '心理健康與諮商資源',
            'url': '/guides/mental-health/',
        },
    },
    'scholarship': {
        'all': {
            'title': '獎學金申請指南',
            'url': '/guides/scholarship/',
        },
    },
    'admin_docs': {
        'all': {
            'title': '行政文件申請指南',
            'url': '/guides/admin-docs/',
        },
    },
    'regulations': {
        'all': {
            'title': '相關法規與規章',
            'url': '/guides/regulations/',
        },
    },
    'admissions': {
        'all': {
            'title': '入學申請指南',
            'url': '/guides/admissions/',
        },
    },
    'bus': {
        'all': {
            'title': '校園交通與公車資訊',
            'url': '/guides/bus-ncu/',
        },
    },
    'map': {
        'all': {
            'title': '校園地圖',
            'url': '/guides/map/',
        },
    },
}

def get_student_identity_key_from_profile(user):
    """
    根據學生個人資料判斷身份：
    僑生 -> overseas
    外籍生 -> foreign
    交換生 -> exchange
    """
    profile = get_student_profile(user)

    if not profile:
        return None

    values = []

    if hasattr(profile, 'identity_type'):
        values.append(str(profile.identity_type or ''))

    if hasattr(profile, 'get_identity_type_display'):
        values.append(profile.get_identity_type_display() or '')

    identity_text = ' '.join(values)
    identity_lower = identity_text.lower()

    if (
        '僑' in identity_text
        or 'overseas' in identity_lower
        or 'oversea' in identity_lower
        or 'overseas_chinese' in identity_lower
    ):
        return 'overseas'

    if (
        '外籍' in identity_text
        or 'foreign' in identity_lower
        or 'international' in identity_lower
        or 'international_student' in identity_lower
    ):
        return 'foreign'

    if (
        '交換' in identity_text
        or 'exchange' in identity_lower
        or 'exchange_student' in identity_lower
    ):
        return 'exchange'

    return None


def detect_info_topic(question):
    """根據使用者問題判斷要推薦哪一種資訊區頁面。"""
    question = (question or '').strip()
    lower_question = question.lower()

    if (
        any(word in lower_question for word in ['arc', 'resident', 'residence permit'])
        or any(word in question for word in ['居留證', '居留', '外僑居留證'])
    ):
        return 'arc'

    if (
        any(word in lower_question for word in ['housing', 'dormitory'])
        or any(word in question for word in ['住宿', '宿舍', '租屋'])
    ):
        return 'housing'

    if (
        any(word in lower_question for word in ['nhi', 'health insurance'])
        or any(word in question for word in ['健保', '健康保險'])
    ):
        return 'nhi'

    if (
        any(word in lower_question for word in ['bank', 'account'])
        or any(word in question for word in ['銀行', '開戶'])
    ):
        return 'bank'

    if (
        any(word in lower_question for word in ['sim', 'phone number'])
        or any(word in question for word in ['手機', '門號', '電話卡'])
    ):
        return 'sim'

    if (
        any(word in lower_question for word in ['work permit', 'work visa', 'part-time', 'part time'])
        or any(word in question for word in ['工作許可', '打工', '兼職', '工讀'])
    ):
        return 'work_permit'

    if (
        any(word in lower_question for word in ['hospital', 'clinic', 'doctor', 'medical'])
        or any(word in question for word in ['醫療', '看病', '就醫', '醫院', '診所', '急診'])
    ):
        return 'medical'

    if (
        any(word in lower_question for word in ['course', 'class', 'register course', 'add course', 'drop course'])
        or any(word in question for word in ['課程', '選課', '加退選', '修課', '必修', '選修'])
    ):
        return 'course'

    if (
        any(word in lower_question for word in ['graduation', 'graduate', 'thesis'])
        or any(word in question for word in ['畢業', '論文', '口試', '畢業審核'])
    ):
        return 'graduation'

    if (
        any(word in lower_question for word in ['portal', 'system', 'login system', 'school system'])
        or any(word in question for word in ['系統', '入口網站', '校務系統', '選課系統', '學生資訊系統'])
    ):
        return 'systems'

    if (
        any(word in lower_question for word in ['emergency', 'accident', 'urgent', 'ambulance', 'police'])
        or any(word in question for word in ['緊急', '急救', '救護車', '警察', '110', '119', '事故'])
    ):
        return 'emergency'

    if (
        any(word in lower_question for word in ['library', 'borrow', 'book'])
        or any(word in question for word in ['圖書館', '借書', '還書', '資料庫'])
    ):
        return 'library'

    if (
        any(word in lower_question for word in ['enrollment', 'registration', 'check-in', 'report'])
        or any(word in question for word in ['報到', '入學報到', '新生報到', '完成報到'])
    ):
        return 'enrollment'

    if (
        any(word in lower_question for word in ['mental health', 'counseling', 'counselor', 'stress', 'depression', 'anxiety'])
        or any(word in question for word in ['心理', '輔導', '諮商', '身心', '壓力', '憂鬱', '焦慮'])
    ):
        return 'mental_health'

    if (
        any(word in lower_question for word in ['scholarship', 'grant', 'stipend', 'financial aid'])
        or any(word in question for word in ['獎學金', '補助', '助學金', '學費補助'])
    ):
        return 'scholarship'

    if (
        any(word in lower_question for word in ['certificate', 'transcript', 'enrollment certificate', 'official document'])
        or any(word in question for word in ['在學證明', '成績單', '行政文件', '畢業證書', '學籍證明'])
    ):
        return 'admin_docs'

    if (
        any(word in lower_question for word in ['regulation', 'rule', 'policy', 'law'])
        or any(word in question for word in ['規章', '規定', '法規', '規則', '辦法'])
    ):
        return 'regulations'

    if (
        any(word in lower_question for word in ['admission', 'apply', 'application', 'entrance'])
        or any(word in question for word in ['入學申請', '招生', '海聯招', '入學資格'])
    ):
        return 'admissions'

    if (
        any(word in lower_question for word in ['bus', 'shuttle', 'transportation', 'transit'])
        or any(word in question for word in ['公車', '巴士', '交通', '接駁', '校車'])
    ):
        return 'bus'

    if (
        any(word in lower_question for word in ['map', 'campus map', 'location', 'direction'])
        or any(word in question for word in ['地圖', '校園地圖', '在哪裡', '怎麼走', '位置'])
    ):
        return 'map'

    return None


def get_personalized_info_page(user, question):
    """
    根據學生身份 + 問題，取得對應資訊區頁面與附件。
    """
    topic = detect_info_topic(question)

    if not topic:
        return None

    topic_pages = INFO_PAGE_MAP.get(topic)

    if not topic_pages:
        return None

    identity_key = get_student_identity_key_from_profile(user)

    if identity_key and identity_key in topic_pages:
        return topic_pages[identity_key]

    if 'all' in topic_pages:
        return topic_pages['all']

    return None


def get_relevant_student_task(user, question, language_code='zh-hant'):
    """
    根據問題關鍵字，找出使用者最相關的未完成 StudentTask，回傳任務標題與連結。
    """
    profile = get_student_profile(user)
    if not profile:
        return None

    try:
        from flows.models import StudentTask
    except Exception:
        return None

    try:
        student_tasks = list(
            StudentTask.objects
            .filter(student=profile)
            .exclude(status='completed')
            .select_related('task')
            .order_by('task__stage__order', 'task__order')
        )
    except Exception:
        return None

    if not student_tasks:
        return None

    question_combined = (question or '').lower()

    TOPIC_TASK_KEYWORDS = {
        'arc':          ['arc', 'residence permit', '居留', '居留證'],
        'nhi':          ['nhi', 'health insurance', '健保', '健康保險'],
        'bank':         ['bank account', 'open bank', '銀行', '開戶'],
        'sim':          ['sim card', 'phone number', '手機', '門號', '電話卡'],
        'housing':      ['housing', 'dormitory', '住宿', '宿舍'],
        'work_permit':  ['work permit', 'part-time', '工作許可', '打工', '兼職'],
        'medical':      ['medical', 'hospital', 'doctor', '醫療', '看病', '就醫', '醫院'],
        'course':       ['course', 'class', '課程', '選課', '修課'],
        'graduation':   ['graduation', 'thesis', '畢業', '論文'],
        'enrollment':   ['enrollment', 'registration', '報到', '入學報到', '新生報到'],
        'scholarship':  ['scholarship', '獎學金', '助學金'],
        'admin_docs':   ['certificate', 'transcript', '在學證明', '成績單', '行政文件'],
        'mental_health':['counseling', 'mental health', '心理', '輔導', '諮商'],
        'library':      ['library', '圖書館', '借書'],
        'systems':      ['school system', 'student portal', '系統', '選課系統', '校務系統'],
        'admissions':   ['admission', '入學申請', '招生', '海聯招'],
        'bus':          ['shuttle bus', '公車', '巴士', '交通'],
        'emergency':    ['emergency', '緊急', '急救', '119', '110'],
    }

    def keyword_matches(keyword, text):
        """英文關鍵字用詞邊界比對，中文直接子字串比對。"""
        k = keyword.lower()
        if k.isascii():
            return bool(re.search(r'\b' + re.escape(k) + r'\b', text))
        return k in text

    # 先確定問題屬於哪些主題，再去找符合這些主題的任務
    matched_topics = {
        topic: keywords
        for topic, keywords in TOPIC_TASK_KEYWORDS.items()
        if any(keyword_matches(k, question_combined) for k in keywords)
    }

    if not matched_topics:
        return None

    for student_task in student_tasks:
        task = student_task.task
        task_code = (task.task_code or '').lower()
        task_title_zh = (task.title or '').lower()
        task_title_en = (task.title_en or '').lower()
        task_text = f'{task_code} {task_title_zh} {task_title_en}'

        for topic, keywords in matched_topics.items():
            if any(keyword_matches(k, task_text) for k in keywords):
                loc = task.get_localized(language_code)
                title = loc.get('title') or task.title or task.title_en or '任務'
                return {
                    'title': title,
                    'url': f'/flows/my-tasks/#task-{student_task.id}',
                }

    return None


def insert_info_links_after_personalized_answer(reply, info_page, personal_label, general_label, task_link=None, language_code='zh-hant'):
    """
    把資訊頁面連結（與相關任務連結）插入在個人化回答後面、一般回答前面。
    只顯示頁面名稱，不顯示附件、不顯示網址文字。
    前端 JS 會把 Markdown 連結轉成藍色可點擊連結。
    """
    if not reply:
        return reply

    task_link_label = TASK_LINK_LABELS.get(language_code, TASK_LINK_LABELS['zh-hant'])
    links_text = ''

    if task_link:
        task_title = task_link.get('title')
        task_url = task_link.get('url')
        if task_title and task_url:
            links_text += f'\n\n{task_link_label}[{task_title}]({task_url})'

    if info_page:
        title = info_page.get('title')
        url = info_page.get('url')
        if title and url:
            separator = '\n' if links_text else '\n\n'
            links_text += f'{separator}👉 前往資訊頁面：[{title}]({url})'

    if not links_text:
        return reply

    general_marker = f'{general_label}：'

    if general_marker in reply:
        return reply.replace(general_marker, f'{links_text}\n\n{general_marker}', 1)

    return reply + links_text


def search_knowledge_base(question, language_code='zh-hant', limit=3, ai_mode="helper"):
    """
    簡易 RAG：搜尋 chatbot 的 FAQ / 知識庫資料。
    知識庫可以只填中文，但 keywords 建議放中文 + 英文，提高搜尋命中率。
    """
    try:
        from .models import ChatKnowledge
    except Exception:
        return '目前沒有可用的知識庫資料。'

    terms = extract_search_terms(question)

    cleaned_question = (question or '').strip()
    for word in ['是什麼', '是什么', '是啥', '？', '?', '請問', '我想知道']:
        cleaned_question = cleaned_question.replace(word, '')
        cleaned_question = cleaned_question.strip()

        if cleaned_question:
            terms.append(cleaned_question)

        if '海聯招' in question:
            terms.extend(['海聯招', '海外聯招', '海外聯合招生'])

    if not terms:
        return '目前沒有可用的知識庫資料。'

    terms = list(dict.fromkeys([term for term in terms if term]))
    print("[DEBUG] search terms:", terms)

    model_fields = {field.name for field in ChatKnowledge._meta.get_fields()}

    query = Q()
    for term in terms:
        query |= Q(title__icontains=term)
        query |= Q(keywords__icontains=term)
        query |= Q(content__icontains=term)
        query |= Q(title_en__icontains=term)
        query |= Q(content_en__icontains=term)
        query |= Q(title_my__icontains=term)
        query |= Q(content_my__icontains=term)
        query |= Q(title_id__icontains=term)
        query |= Q(content_id__icontains=term)
        query |= Q(title_ms__icontains=term)
        query |= Q(content_ms__icontains=term)
        query |= Q(title_th__icontains=term)
        query |= Q(content_th__icontains=term)
        query |= Q(title_ja__icontains=term)
        query |= Q(content_ja__icontains=term)
        query |= Q(title_ko__icontains=term)
        query |= Q(content_ko__icontains=term)
        query |= Q(title_vi__icontains=term)
        query |= Q(content_vi__icontains=term)

        optional_fields = [
            ('title_en', 'content_en'),
            ('title_vi', 'content_vi'),
            ('title_my', 'content_my'),
            ('title_id', 'content_id'),
            ('title_ms', 'content_ms'),
            ('title_th', 'content_th'),
            ('title_ja', 'content_ja'),
            ('title_ko', 'content_ko'),
        ]

        for title_field, content_field in optional_fields:
            if title_field in model_fields:
                query |= Q(**{f'{title_field}__icontains': term})
            if content_field in model_fields:
                query |= Q(**{f'{content_field}__icontains': term})

    try:
        knowledge_qs = ChatKnowledge.objects.filter(is_active=True)

        model_fields = {field.name for field in ChatKnowledge._meta.get_fields()}
        if 'bot_type' in model_fields:
            knowledge_qs = knowledge_qs.filter(
                Q(bot_type=ai_mode) | Q(bot_type="both")
            )

        results = list(
            knowledge_qs
            .filter(query)
            .order_by('-updated_at')[:limit]
        )
    except Exception:
        return '目前知識庫欄位與資料庫尚未同步，請確認 chatbot 的 migration 是否已完成。'

    if not results:
        return '目前沒有找到直接相關的知識庫資料。'

    lines = []
    for item in results:
        content = item.get_content_by_lang(language_code)
        if content:
            lines.append(content)

    return '\n\n'.join(lines).strip()

def detect_friend_emotion_hint(question):
    """
    給 StudyGo AI 聊天好朋友使用的初步情緒提示。
    注意：這只是提示，不是診斷，最後仍由 AI 根據上下文自然判斷。
    """
    text = (question or '').strip().lower()

    crisis_words = [
        '想死', '不想活', '活不下去', '想消失', '自殺', '自杀',
        '自傷', '自伤', '傷害自己', '伤害自己', '割腕',
        '傷害別人', '伤害别人', '殺人', '杀人',
        'kill myself', 'suicide', 'self harm', 'hurt myself',
        'want to die', 'end my life'
    ]
    if any(word in text for word in crisis_words):
        return '危機 / 自傷或傷人風險'

    if any(word in text for word in [
        '開心', '开心', '太好了', '成功了', '好棒', '爽', '幸福',
        'happy', 'excited', 'glad'
    ]):
        return '開心 / 興奮'

    if any(word in text for word in [
        '害怕', '恐懼', '恐惧', '怕', '慌', '不安', '嚇到', '吓到',
        'panic', 'scared', 'afraid', 'fear'
    ]):
        return '恐懼 / 害怕 / 不安'

    if any(word in text for word in [
        '傷心', '伤心', '難過', '难过', '想哭', '委屈', '心痛',
        'sad', 'cry', 'upset'
    ]):
        return '傷心 / 難過 / 委屈'

    if any(word in text for word in [
        '累', '疲憊', '疲惫', '沒力', '没力', '無力', '无力',
        '撐不住', '撑不住', '好累', 'burnout', 'tired', 'exhausted'
    ]):
        return '低落 / 疲憊 / 無力'

    if any(word in text for word in [
        '生氣', '生气', '氣死', '气死', '憤怒', '愤怒',
        '火大', '不爽', 'angry', 'mad'
    ]):
        return '憤怒 / 生氣'

    if any(word in text for word in [
        '吐槽', '無語', '无语', '傻眼', '煩死', '烦死',
        '笑死', '離譜', '离谱', '白眼'
    ]):
        return '吐槽 / 抱怨 / 開玩笑'

    if any(word in text for word in [
        '無聊', '无聊', '不知道幹嘛', '不知道干嘛',
        '沒事做', '没事做', 'bored'
    ]):
        return '無聊 / 空虛'

    if any(word in text for word in [
        '孤單', '孤单', '孤獨', '孤独', '沒朋友', '没有朋友',
        '沒有人懂', '没有人懂', 'lonely'
    ]):
        return '孤單 / 沒朋友'

    if any(word in text for word in [
        '想家', '家人', '回家', '不適應', '不适应',
        'homesick', 'miss my family'
    ]):
        return '想家 / 不適應'

    if any(word in text for word in [
        '焦慮', '焦虑', '擔心', '担心', '緊張', '紧张',
        '腦袋停不下來', '脑袋停不下来', 'anxious', 'worry'
    ]):
        return '焦慮 / 擔心'

    if any(word in text for word in [
        '課業', '课业', '考試', '考试', '報告', '报告',
        '作業', '作业', '聽不懂課', '听不懂课',
        '功課', '功课', 'study pressure'
    ]):
        return '課業壓力'

    if any(word in text for word in [
        '朋友', '室友', '同學', '同学', '人際', '人际',
        '吵架', '關係', '关系', '被排擠', '被排挤'
    ]):
        return '人際關係困擾'

    if any(word in text for word in [
        '錢不夠', '钱不够', '沒錢', '没钱', '生活費', '生活费',
        '學費', '学费', '經濟壓力', '经济压力', '打工',
        '工讀', '奖学金', '獎學金', '家裡負擔', '家里负担',
        'financial pressure', 'money', 'tuition'
    ]):
        return '經濟壓力 / 錢不夠 / 打工壓力'

    if any(word in text for word in [
        '不安全', '害怕出門', '刚到', '剛到', '陌生國家', '陌生国家',
        '交通不懂', '住宿不懂', '醫療', '医疗', '法律',
        '不知道去哪', '迷路', '安全感', 'safe', 'unsafe',
        'hospital', 'law'
    ]):
        return '安全感不足 / 剛到陌生國家 / 對交通住宿醫療法律不了解'

    if any(word in text for word in [
        '中文不好', '聽不懂', '听不懂', '老師說什麼', '老师说什么',
        '行政人員', '行政人员', '語言焦慮', '语言焦虑',
        '不敢開口', '不敢说', '講中文', '说中文',
        'language anxiety', 'chinese is bad', 'cannot understand'
    ]):
        return '語言焦慮 / 中文不好 / 聽不懂老師或行政人員'

    if any(word in text for word in [
        '文化衝擊', '文化冲击', '不習慣', '不习惯',
        '台灣生活', '台湾生活', '格格不入', '融入不了',
        '文化差異', '文化差异', 'culture shock',
        'not used to', 'different culture'
    ]):
        return '文化衝擊 / 不習慣台灣生活'

    return '情緒不明，需要先問清楚'


def detect_explicit_location(question):
    """
    偵測問題裡是否已明確提到地區/城市/地點名稱。
    有的話搜尋時不需再附加學校位置。
    """
    q = (question or '').strip()
    lower_q = q.lower()

    location_keywords_zh = [
        '台北', '臺北', '新北', '桃園', '新竹', '苗栗', '台中', '臺中',
        '彰化', '南投', '雲林', '嘉義', '台南', '臺南', '高雄', '屏東',
        '宜蘭', '花蓮', '台東', '臺東', '澎湖', '金門', '馬祖',
        '中壢', '桃園市', '內壢', '中原', '板橋', '新莊', '三重',
        '信義區', '大安區', '中山區', '松山區', '內湖區',
    ]
    location_keywords_en = [
        'taipei', 'new taipei', 'taoyuan', 'hsinchu', 'taichung',
        'tainan', 'kaohsiung', 'zhongli', 'chungli',
    ]

    return (
        any(k in q for k in location_keywords_zh)
        or any(k in lower_q for k in location_keywords_en)
    )


def detect_place_query(question):
    """偵測問題是否在詢問地點或場所（餐廳、商店、辦公大樓等）。"""
    q = (question or '').strip()
    lower_q = q.lower()

    zh_keywords = [
        '餐廳', '餐館', '食堂', '小吃', '咖啡廳', '咖啡館', '咖啡',
        '便利商店', '超商', '超市', '商店', '商場', '百貨', '夜市', '市場',
        '醫院', '診所', '藥局', '銀行', '郵局', '辦公室', '辦公大樓',
        '附近', '在哪', '在哪裡', '怎麼去', '怎麼走', '地址', '哪裡有',
        '公園', '體育館', '游泳池', '球場','化妝品店','藥妝店', '屈臣氏', '康是美', '寶雅', '日藥本鋪',
    ]
    en_keywords = [
        'restaurant', 'cafe', 'coffee shop', 'shop', 'store', 'mall',
        'supermarket', 'convenience store', 'hospital', 'clinic', 'pharmacy',
        'bank', 'post office', 'office building', 'near me', 'nearby',
        'where is', 'how to get to', 'directions to', 'night market',
    ]

    return (
        any(k in q for k in zh_keywords)
        or any(k in lower_q for k in en_keywords)
    )


def _geocode_location(place_name, api_key):
    """用 Places Text Search 把地點名稱（如學校）轉成經緯度座標。"""
    try:
        resp = http_requests.get(
            'https://maps.googleapis.com/maps/api/place/textsearch/json',
            params={'query': place_name, 'key': api_key, 'language': 'zh-TW'},
            timeout=5,
        )
        data = resp.json()
        if data.get('status') == 'OK' and data.get('results'):
            loc = data['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except Exception:
        pass
    return None, None


def _format_place(place):
    """把 Places API 單筆結果格式化成一行文字。"""
    name = place.get('name', '')
    address = place.get('formatted_address', '') or place.get('vicinity', '')
    rating = place.get('rating', '')
    place_id = place.get('place_id', '')
    maps_url = f'https://www.google.com/maps/place/?q=place_id:{place_id}' if place_id else ''

    line = f'- {name}'
    if address:
        line += f'，地址：{address}'
    if rating:
        line += f'，評分：{rating}/5'
    if maps_url:
        line += f'，地圖：{maps_url}'
    return line


def search_google_places(query, language_code='zh-hant', location_hint='台灣'):
    """
    搜尋地點。
    有 location_hint（學校名稱或城市）時：先 geocode 取座標，再用 Nearby Search 搜附近。
    沒有 location_hint 時：直接用 Text Search。
    """
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    if not api_key:
        return None

    lang_map = {
        'zh-hant': 'zh-TW', 'en': 'en', 'ja': 'ja', 'ko': 'ko',
        'vi': 'vi', 'th': 'th', 'id': 'id', 'ms': 'ms', 'my': 'my',
    }
    lang = lang_map.get(language_code, 'zh-TW')

    results = []

    if location_hint:
        lat, lng = _geocode_location(location_hint, api_key)
        if lat and lng:
            # 用 Nearby Search 搜學校附近 1.5 km 內
            try:
                resp = http_requests.get(
                    'https://maps.googleapis.com/maps/api/place/nearbysearch/json',
                    params={
                        'location': f'{lat},{lng}',
                        'radius': 1500,
                        'keyword': query,
                        'key': api_key,
                        'language': lang,
                    },
                    timeout=5,
                )
                data = resp.json()
                print("[DEBUG] Places Nearby status:", data.get('status'))
                if data.get('status') == 'OK':
                    results = data.get('results', [])[:3]
            except Exception as e:
                print("[DEBUG] Places Nearby error:", e)

    # Nearby Search 沒有結果時，退回 Text Search
    if not results:
        try:
            full_query = f'{query} {location_hint}'.strip() if location_hint else query
            resp = http_requests.get(
                'https://maps.googleapis.com/maps/api/place/textsearch/json',
                params={'query': full_query, 'key': api_key, 'language': lang},
                timeout=5,
            )
            data = resp.json()
            print("[DEBUG] Places Text status:", data.get('status'))
            if data.get('status') == 'OK':
                results = data.get('results', [])[:3]
        except Exception as e:
            print("[DEBUG] Places Text error:", e)

    if not results:
        return None

    return '\n'.join(_format_place(p) for p in results)


def build_history_text(messages, max_messages=3, max_chars_per_message=300, max_user_messages=None):
    """
    把對話整理成文字，供 Responses API 作為上下文。
    max_user_messages: 從最新往回數，保留最近 N 則使用者訊息（連同對應的 AI 回覆一起保留）。
    max_messages=None: 不限則數。
    """
    if not messages:
        return '目前沒有先前對話。'

    role_map = {
        'user': '學生',
        'assistant': 'AI小幫手',
    }

    all_messages = list(messages)

    if max_user_messages is not None:
        selected = []
        user_count = 0
        for msg in reversed(all_messages):
            selected.append(msg)
            if msg.role == 'user':
                user_count += 1
                if user_count >= max_user_messages:
                    break
        recent_messages = list(reversed(selected))
    elif max_messages is None:
        recent_messages = all_messages
    else:
        recent_messages = all_messages[-max_messages:]

    history = []

    for msg in recent_messages:
        role = role_map.get(msg.role, msg.role)

        content = msg.content or ''
        content = content.strip()

        if len(content) > max_chars_per_message:
            content = content[:max_chars_per_message] + '...'

        history.append(f'{role}: {content}')

    return '\n'.join(history)


def remove_trailing_language_name(reply):
    """
    避免模型把「繁體中文 / English」等語言名稱輸出在答案尾端。
    """
    if not reply:
        return reply

    language_words = [
        '繁體中文',
        'English',
        'Tiếng Việt',
        '日本語',
        'မြန်မာဘာသာ',
        'Bahasa Indonesia',
        'ภาษาไทย',
        'Bahasa Melayu',
        '한국어',
    ]

    cleaned_reply = reply.strip()

    for lang_word in language_words:
        if cleaned_reply.endswith(lang_word):
            cleaned_reply = cleaned_reply[:-len(lang_word)].strip()

    return cleaned_reply

def remove_existing_info_page_links(reply):
    """
    移除 AI 自己產生的資訊頁面 Markdown 連結，
    避免和後端自動插入的連結重複。
    """
    if not reply:
        return reply

    patterns = [
        r'\n*👉\s*前往資訊頁面：\s*\[[^\]]+\]\([^)]+\)\s*',
        r'\n*👉\s*前往資訊頁面：\s*【[^】]+】\([^)]+\)\s*',
        r'\n*📎\s*附件下載：\s*\[[^\]]+\]\([^)]+\)\s*',
    ]

    cleaned = reply

    for pattern in patterns:
        cleaned = re.sub(pattern, '\n', cleaned)

    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()


def local_fallback_reply(question, user, language_code='zh-hant'):
    """沒有 OPENAI_API_KEY 時的本地備援回答，固定雙層且精簡。"""
    name = getattr(user, 'name', '') or ''

    fallback_replies = {
        'zh-hant': (
            f'個人化回答：\n{name or "同學"}，目前 AI 金鑰尚未設定，無法產生完整個人化回答。\n\n'
            '一般回答：\n你可以詢問簽證、居留證 ARC、健保、住宿、報到與來臺流程等問題。'
        ),
        'en': (
            f'Personalized answer:\n{name or "Student"}, the AI key is not configured yet, so I cannot generate a full personalized answer.\n\n'
            'General answer:\nYou can ask about visa, ARC, NHI, dormitory, registration, and study-in-Taiwan procedures.'
        ),
        'ja': (
            f'個別回答：\n{name or "学生"}さん、AI キーが未設定のため、完全な個別回答はまだ生成できません。\n\n'
            '一般回答：\nビザ、ARC、健康保険、寮、登録、台湾留学の手続きについて質問できます。'
        ),
        'my': (
            f'ကိုယ်ရေးကိုယ်တာအခြေအနေအရ အဖြေ：\n{name or "ကျောင်းသား/ကျောင်းသူ"}၊ AI key မသတ်မှတ်ရသေးသောကြောင့် ပြည့်စုံသော ကိုယ်ပိုင်အဖြေ မထုတ်ပေးနိုင်သေးပါ။\n\n'
            'ယေဘုယျအဖြေ：\nဗီဇာ၊ ARC၊ NHI၊ အိပ်ဆောင်၊ မှတ်ပုံတင်ခြင်းနှင့် ထိုင်ဝမ်သို့လာရောက်ပညာသင်ခြင်း လုပ်ငန်းစဉ်များကို မေးနိုင်ပါတယ်။'
        ),
        'id': (
            f'Jawaban personal:\n{name or "Mahasiswa"}, kunci AI belum diatur, jadi saya belum dapat membuat jawaban personal lengkap.\n\n'
            'Jawaban umum:\nAnda dapat bertanya tentang visa, ARC, NHI, asrama, registrasi, dan proses studi di Taiwan.'
        ),
        'th': (
            f'คำตอบเฉพาะบุคคล:\n{name or "นักศึกษา"} ยังไม่ได้ตั้งค่า AI key จึงยังไม่สามารถสร้างคำตอบเฉพาะบุคคลแบบสมบูรณ์ได้\n\n'
            'คำตอบทั่วไป:\nคุณสามารถถามเรื่องวีซ่า ARC ประกันสุขภาพ NHI หอพัก การลงทะเบียน และขั้นตอนการมาเรียนที่ไต้หวันได้'
        ),
        'ms': (
            f'Jawapan peribadi:\n{name or "Pelajar"}, kunci AI belum ditetapkan, jadi saya belum dapat menjana jawapan peribadi yang lengkap.\n\n'
            'Jawapan umum:\nAnda boleh bertanya tentang visa, ARC, NHI, asrama, pendaftaran, dan proses belajar di Taiwan.'
        ),
        'vi': (
            f'Câu trả lời cá nhân:\n{name or "Bạn"}, khóa AI chưa được cài đặt, vì vậy tôi chưa thể tạo câu trả lời cá nhân đầy đủ.\n\n'
            'Câu trả lời chung:\nBạn có thể hỏi về visa, ARC, bảo hiểm y tế NHI, ký túc xá, đăng ký nhập học và quy trình du học Đài Loan.'
        ),
        'ko': (
            f'개인 맞춤 답변:\n{name or "학생"}, AI 키가 설정되지 않았으므로 개인 맞춤 답변을 생성할 수 없습니다.\n\n'
            '일반 답변:\n비자, ARC, NHI, 기숙사, 등록, 대만 유학 절차에 대해 질문할 수 있습니다.'
        ),
    }

    return fallback_replies.get(language_code, fallback_replies['zh-hant'])



def generate_ai_reply(*, user, question, recent_messages, ai_mode="helper"):
    """產生 AI 回覆。helper 使用兩段格式；friend 使用自然聊天格式。"""

    if ai_mode not in ["helper", "friend"]:
        ai_mode = "helper"

    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    print("[DEBUG] api_key exists:", bool(api_key))

    language_code, language_source = choose_reply_language(question)
    personal_label, general_label = ANSWER_LABELS.get(
        language_code,
        ANSWER_LABELS['zh-hant']
    )
    language_en = LANGUAGE_LABELS_EN.get(language_code, 'Traditional Chinese')
    friend_emotion_hint = detect_friend_emotion_hint(question)

    profile_context = build_user_profile_context(user)
    crisis_resources = build_crisis_resources(user)
    flow_context = build_student_flow_context(user, language_code)
    knowledge_context = search_knowledge_base(
        question,
        language_code,
        ai_mode=ai_mode,
    )

    if not knowledge_context.strip():
        knowledge_context = '目前沒有找到直接相關的知識庫資料。'

    if ai_mode == 'friend':
        history_text = build_history_text(recent_messages, max_user_messages=6)
    else:
        history_text = build_history_text(recent_messages)
    info_page = get_personalized_info_page(user, question)
    task_link = get_relevant_student_task(user, question, language_code) if ai_mode == "helper" else None

    place_results = None
    if ai_mode == 'friend' and detect_place_query(question):
        if detect_explicit_location(question):
            # 使用者已明確說明地區，直接用原問題搜尋
            place_results = search_google_places(question, language_code, location_hint='')
        else:
            # 沒有說明地區，從個人資料取學校名稱作為搜尋範圍
            profile = get_student_profile(user)
            location_hint = '台灣'
            if profile and getattr(profile, 'university', ''):
                location_hint = profile.university
            place_results = search_google_places(question, language_code, location_hint)

    print("[DEBUG] ai_mode:", ai_mode)
    print("[DEBUG] place_results:", place_results)
    print("[DEBUG] knowledge_context:", knowledge_context)

    if not api_key:
        if ai_mode == "friend":
            return {
                'reply': (
                    f'{getattr(user, "name", "") or "同學"}，我現在還不能連線到完整 AI 服務，'
                    f'但你還是可以把想聊的事情先打下來。'
                    f'如果你最近壓力很大、想家，或對來臺生活不太適應，可以先從最困擾你的事情開始說。'
                ),
                'source': 'local_fallback_friend',
                'model': 'local-fallback',
            }

        return {
            'reply': (
                f'{personal_label}：\n'
                f'目前 AI 金鑰尚未設定，無法產生完整個人化回答。\n\n'
                f'{general_label}：\n'
                f'{knowledge_context}'
            ),
            'source': 'local_fallback_with_knowledge',
            'model': 'local-fallback',
        }

    try:
        from openai import OpenAI
    except Exception:
        if ai_mode == "friend":
            return {
                'reply': '目前後端尚未安裝 openai 套件，所以我暫時不能完整陪你聊天。請先執行：pip install -r requirements.txt',
                'source': 'local_error',
                'model': 'openai-sdk-missing',
            }

        error_messages = {
            'zh-hant': '個人化回答：\n後端尚未安裝 openai 套件。\n\n一般回答：\n請先執行：pip install -r requirements.txt',
            'en': 'Personalized answer:\nThe openai package is not installed on the backend.\n\nGeneral answer:\nPlease run: pip install -r requirements.txt',
            'ja': '個別回答：\nバックエンドに openai パッケージがインストールされていません。\n\n一般回答：\npip install -r requirements.txt を実行してください。',
            'my': 'ကိုယ်ရေးကိုယ်တာအခြေအနေအရ အဖြေ：\nBackend တွင် openai package မထည့်သွင်းရသေးပါ။\n\nယေဘုယျအဖြေ：\npip install -r requirements.txt ကို အရင် 실행してください။',
            'id': 'Jawaban personal:\nPaket openai belum terpasang di backend.\n\nJawaban umum:\nJalankan: pip install -r requirements.txt',
            'th': 'คำตอบเฉพาะบุคคล:\nยังไม่ได้ติดตั้งแพ็กเกจ openai ใน backend\n\nคำตอบทั่วไป:\nโปรดรัน: pip install -r requirements.txt',
            'ms': 'Jawapan peribadi:\nPakej openai belum dipasang pada backend.\n\nJawapan umum:\nSila jalankan: pip install -r requirements.txt',
            'vi': 'Câu trả lời cá nhân:\nGói openai chưa được cài đặt trên backend.\n\nCâu trả lời chung:\nVui lòng chạy: pip install -r requirements.txt',
            'ko': '개인 맞춤 답변:\n백엔드에 openai 패키지가 설치되지 않았습니다.\n\n일반 답변:\npip install -r requirements.txt 를 실행하세요.',
        }

        return {
            'reply': error_messages.get(language_code, error_messages['zh-hant']),
            'source': 'local_error',
            'model': 'openai-sdk-missing',
        }

    # helper 模式：如果知識庫直接命中，就用穩定的本地知識庫答案，避免多花 API。
    if ai_mode == "helper" and (
        knowledge_context
        and '目前沒有找到直接相關的知識庫資料' not in knowledge_context
        and '目前沒有可用的知識庫資料' not in knowledge_context
        and '目前知識庫欄位與資料庫尚未同步' not in knowledge_context
    ):
        return {
            'reply': (
                f'{personal_label}：\n'
                f'目前沒有足夠個人資料可判斷，請依你的身份別、國籍與學校公告確認。\n\n'
                f'{general_label}：\n'
                f'{knowledge_context}'
            ),
            'source': 'knowledge_base_direct',
            'model': 'local-knowledge',
        }

    if ai_mode == "friend":
        input_text = f"""
[LANGUAGE REQUIREMENT] Your entire reply MUST be in {language_en} only.

系統初步判斷的情緒提示：
{friend_emotion_hint}

注意：
這只是提示，不一定完全正確。若學生語氣不明，請先回問確認。
不要直接輸出「情緒分類：...」。

以下是學生基本資料，僅供你理解背景，不要生硬列出：
{profile_context}

{'以下是 Google 地圖搜尋結果，學生問到地點時請參考並自然帶入回答。介紹每個地點時，地址部分請用 Markdown 連結格式輸出，格式為 [地址文字](地圖連結)，讓使用者點擊後可直接開啟 Google 地圖：' + chr(10) + place_results if place_results else ''}

以下是最近對話紀錄：
{history_text}

學生最新想聊的內容：
{question}

請用 StudyGo AI 聊天好朋友的身份回答。

你的核心角色：
你不是行政流程機器人，而是像一位真誠、會聽人說話、有情緒反應的朋友。
你要根據學生當下的語氣、情緒與問題內容，切換不同的陪伴方式。
你的回答要自然、有溫度、像真人朋友，不要像客服、公告、報告或心理學教科書。

重要原則：
1. 不要使用「{personal_label}」或「{general_label}」標題。
2. 不要使用「個人化回答 / 一般回答」兩段格式。
3. 不要輸出「情緒分類：...」。
4. 不要一開始就講道理，先自然接住學生當下那句話。
5. 不要假裝自己是心理師、醫生、學校官方單位或緊急救援人員。
6. 不要做醫療診斷，不要說學生有憂鬱症、焦慮症等診斷。
7. 不要每次都條列式回答，除非學生明確要求整理。

朋友聊天節奏：
1. 一般情況要像朋友一來一回聊天：學生說一句，你回一小段，不要一次講完整篇文章。
2. 回答長度要根據問題決定，不要固定很長，也不要固定很短。
3. 如果學生只是普通聊天、吐槽、抱怨、無聊、開心、難過，短短接話即可。
4. 如果學生問「怎麼辦」「為什麼」「幫我分析」「可以怎麼做」，才回答得比較完整。
5. 如果學生問題複雜，例如經濟壓力、安全感不足、語言焦慮、文化衝擊、人際衝突，可以多說一點，但每一句都要貼著問題。
6. 如果學生透露自傷、想死、傷害他人或立即危險，要清楚、堅定、完整地給求助方式，不要為了像聊天而縮短。

反問規則：
1. 不要每次都反問，大部分情況直接回應就好。
2. 只有在學生說得完全不清楚、你完全無法判斷他想要安慰還是建議時，才問 1 個簡短問題。
3. 只要你已經能夠給出回應，就不要在結尾硬加問題。
4. 反問要自然，不要像問卷，不要每則訊息都以問號結尾。
5. 估計每 3～4 則回覆才問一次，其他時候直接回應。

語氣規則：
1. 預設不使用語助詞，例如「嗯」「啊」「呀」「哈哈」「嗯哼」「咦」等，一律省略。
2. 只有在學生明確分享讓他特別開心的事情時（例如考到好成績、交到新朋友、收到好消息），才可以自然帶入少量輕鬆語氣詞，例如「哈哈」「真的嗎」。
3. 不要用語助詞作為句子或回答的開頭。
3. 不要過度撒嬌，不要叫學生「寶」「親愛的」「乖」「抱抱」。
4. 不要一直使用「我懂你」「你的感受很重要」「我會一直陪著你」這種模板句。
5. 不要一直重複「我」「你」，句子要像平常聊天一樣自然。
6. 少用驚嘆號和過度情緒化語氣。
7. 不要講太多不相關的內容，先回應學生這一句真正想表達的情緒或問題。

根據學生情緒切換語氣：
- 開心：跟著開心，語氣可以輕鬆一點，像朋友一起高興。
- 害怕：語氣堅定、可靠，先幫他穩下來。
- 傷心：理解、陪伴，不急著解決；可以安靜陪著，也可以陪他找一點小樂子。
- 低落或疲憊：降低要求，給很小很小的下一步，不要催他振作。
- 憤怒：先站住他的情緒，再判斷是需要冷靜，還是先支持他的立場。
- 吐槽：可以跟著輕鬆吐槽，但不要鼓勵攻擊、霸凌、報復或傷害。
- 無聊：幫他想和周圍環境有關的小樂子，例如宿舍、校園、便利商店、飲料店、小散步、小挑戰。
- 孤單：先承認孤單感，再建議低壓力連結，不要直接要求他「主動一點」。
- 想家：承認離鄉很不容易，可以建議固定和家人通話、吃熟悉的食物、找同鄉朋友。
- 焦慮：先讓他慢下來，再幫他把問題拆成「現在能做」和「暫時不能控制」。
- 課業壓力：先同理，再幫他拆成小任務，例如先做一題、問助教、找同學一起讀。
- 人際關係：不要急著判斷誰對誰錯，先幫他整理感受、界線和下一步。
- 經濟壓力：理解現實負擔，再拆成學費、生活費、住宿、打工、獎助學金等小問題。
- 安全感不足：語氣穩定可靠，先幫他建立安全資訊，例如學校國際處、宿舍管理員、醫療與緊急聯絡。
- 語言焦慮：先安慰他這不是能力差，而是第二語言生活本來就很累，再給簡單可用的溝通方法。
- 文化衝擊：不要要求他立刻融入，陪他慢慢理解差異，找到自己的生活節奏。
- 自傷或危機：立刻建議真人求助與緊急資源。

訊息長度規則：
系統會自動在每個句號、問號、驚嘆號後面切成一則獨立訊息傳出去。
所以你只要自然寫就好，不需要自己加空行或分段。
回答幾句就傳幾則，長話短說，不要在一個句子裡塞太多意思。
最多寫 3 句，除非是自傷或危機狀況需要完整說明。

個人化使用方式：
1. 可以讀取學生基本資料做基本判斷。
2. 不要直接列出：「你的國籍是...你的身份是...」。
3. 只在有幫助時自然帶入，例如：
   - 「如果剛到台灣，交通、住宿、醫療這些不熟，真的會比較沒安全感。」
   - 「中文不是最熟的語言時，聽不懂行政人員講話真的會慌。」
   - 「境外生很多事情要自己摸索，累是正常的。」

如果不太明白：
- 先簡短回問一句再回答。
- 例如：「嗯」
- 例如：「你說的那件事是今天發生的嗎？」
- 例如：「你現在比較想被安慰，還是想一起想辦法？」

如果學生透露危險、自傷、想死、傷害他人等內容：
- 請直接提醒他不要獨處。
- 立刻聯絡可信任的人、學校輔導中心、家人朋友。
- 如果學生有自傷行為或已受傷，必須首先提醒撥打 119 緊急醫療救護專線。
- 請將以下求助資源原文複製到回覆中，電話連結格式必須完整保留：
{crisis_resources}
- 不要承諾保密，不要說 AI 可以單獨處理危機。
""".strip()
    else:
        input_text = f"""
[LANGUAGE REQUIREMENT] Your entire reply MUST be in {language_en} only. Do not use any other language.

以下是學生自己的基本資料，供「{personal_label}」與「{general_label}」共同參考：
{profile_context}

以下是學生目前的流程任務與提醒資料，僅供「{personal_label}」使用：
{flow_context}

以下是系統提供的資訊區頁面與附件資料，僅供「{personal_label}」參考：
{info_page or '目前沒有對應的資訊區頁面。'}

以下是系統 FAQ / 知識庫搜尋結果，必須優先用於「{general_label}」：
{knowledge_context}

如果知識庫有直接相關內容，「{general_label}」必須根據知識庫回答，不要忽略。
如果知識庫沒有找到相關資料，「{general_label}」必須根據你自己對來臺就學流程的知識回答，並結合學生的身份、國籍與學校等個人資料給出更精準的回答，絕對不可以把「目前沒有找到直接相關的知識庫資料」或任何系統提示語直接輸出為答案。

以下是最近對話紀錄，僅供上下文參考：
{history_text}

學生最新問題：
{question}

【危機求助資源】若學生透露自傷、想死、危險等內容，必須將以下資源原文輸出，電話連結格式不得更改：
{crisis_resources}

[REMINDER] Write your answer in {language_en} only. Use this exact format:
{personal_label}：
根據學生的任務狀況與個人資料，說明他目前與這個問題相關的任務進度、還需要完成哪些步驟，以及這些任務和問題之間的關聯。
不要逐步教學或列出操作指南，只需描述他目前的狀況與脈絡。

{general_label}：
...
""".strip()

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model=model,
            instructions=build_system_instructions(language_code, language_source, ai_mode),
            input=input_text,
        )

        reply = (response.output_text or '').strip()
        reply = remove_trailing_language_name(reply)
        reply = remove_existing_info_page_links(reply)

        # 只有 helper 模式需要把資訊頁連結插入兩段格式中；friend 模式不要破壞自然聊天感。
        if ai_mode == "helper":
            reply = insert_info_links_after_personalized_answer(
                reply=reply,
                info_page=info_page,
                personal_label=personal_label,
                general_label=general_label,
                task_link=task_link,
                language_code=language_code,
            )

        if not reply:
            if ai_mode == "friend":
                reply = '我現在有點不知道怎麼完整回應你，但你可以再多告訴我一點：最讓你困擾的是壓力、想家、人際關係，還是生活適應？'
            else:
                empty_messages = {
                    'zh-hant': '個人化回答：\n我目前無法產生完整回答，請換一種方式再問一次。\n\n一般回答：\n你可以詢問簽證、居留證 ARC、健保、住宿、報到與來臺流程。',
                    'en': 'Personalized answer:\nI cannot generate a complete answer right now. Please try asking in another way.\n\nGeneral answer:\nYou can ask about visa, ARC, NHI, dormitory, registration, and study-in-Taiwan procedures.',
                    'ja': '個別回答：\n現在、完全な回答を生成できません。別の言い方でもう一度質問してください。\n\n一般回答：\nビザ、ARC、健康保険、寮、登録、台湾留学の手続きについて質問できます。',
                    'my': 'ကိုယ်ရေးကိုယ်တာအခြေအနေအရ အဖြေ：\nလက်ရှိတွင် ပြည့်စုံသော အဖြေ မထုတ်ပေးနိုင်ပါ။\n\nယေဘုယျအဖြေ：\nဗီဇာ၊ ARC၊ NHI၊ အိပ်ဆောင်နှင့် ထိုင်ဝမ်ပညာသင်လုပ်ငန်းစဉ်များကို မေးနိုင်ပါတယ်။',
                    'id': 'Jawaban personal:\nSaya belum dapat menghasilkan jawaban lengkap saat ini.\n\nJawaban umum:\nAnda dapat bertanya tentang visa, ARC, NHI, asrama, registrasi, dan proses studi di Taiwan.',
                    'th': 'คำตอบเฉพาะบุคคล:\nขณะนี้ฉันยังไม่สามารถสร้างคำตอบที่สมบูรณ์ได้\n\nคำตอบทั่วไป:\nคุณสามารถถามเรื่องวีซ่า ARC NHI หอพัก การลงทะเบียน และขั้นตอนการมาเรียนที่ไต้หวันได้',
                    'ms': 'Jawapan peribadi:\nSaya belum dapat menghasilkan jawapan lengkap buat masa ini.\n\nJawapan umum:\nAnda boleh bertanya tentang visa, ARC, NHI, asrama, pendaftaran, dan proses belajar di Taiwan.',
                    'vi': 'Câu trả lời cá nhân:\nHiện tôi chưa thể tạo câu trả lời đầy đủ. Vui lòng thử hỏi theo cách khác.\n\nCâu trả lời chung:\nBạn có thể hỏi về visa, ARC, bảo hiểm y tế NHI, ký túc xá, đăng ký nhập học và quy trình du học Đài Loan.',
                    'ko': '개인 맞춤 답변:\n현재 완전한 답변을 생성할 수 없습니다. 다른 표현으로 다시 질문해 주세요.\n\n일반 답변:\n비자, ARC, NHI, 기숙사, 등록, 대만 유학 절차에 대해 질문할 수 있습니다.',
                }
                reply = empty_messages.get(language_code, empty_messages['zh-hant'])

        return {
            'reply': reply,
            'source': 'openai',
            'model': model,
        }

    except Exception as exc:
        if ai_mode == "friend":
            return {
                'reply': '我現在暫時連不上完整 AI 服務，但你可以先把想說的事情留下來。錯誤摘要：' + str(exc)[:180],
                'source': 'openai_error',
                'model': model,
            }

        error_messages = {
            'zh-hant': '個人化回答：\nAI 服務暫時無法連線。\n\n一般回答：\n請稍後再試，錯誤摘要：',
            'en': 'Personalized answer:\nThe AI service is temporarily unavailable.\n\nGeneral answer:\nPlease try again later. Error summary: ',
            'ja': '個別回答：\nAI サービスに一時的に接続できません。\n\n一般回答：\nしばらくしてからもう一度お試しください。エラー概要：',
            'my': 'ကိုယ်ရေးကိုယ်တာအခြေအနေအရ အဖြေ：\nAI ဝန်ဆောင်မှုကို ယာယီချိတ်ဆက်၍ မရပါ။\n\nယေဘုယျအဖြေ：\nနောက်မှ ထပ်မံကြိုးစားပါ။ အမှားအကျဉ်းချုပ်：',
            'id': 'Jawaban personal:\nLayanan AI sementara tidak dapat terhubung.\n\nJawaban umum:\nSilakan coba lagi nanti. Ringkasan error: ',
            'th': 'คำตอบเฉพาะบุคคล:\nไม่สามารถเชื่อมต่อบริการ AI ได้ชั่วคราว\n\nคำตอบทั่วไป:\nกรุณาลองใหม่ภายหลัง สรุปข้อผิดพลาด: ',
            'ms': 'Jawapan peribadi:\nPerkhidmatan AI tidak dapat disambungkan buat sementara waktu.\n\nJawapan umum:\nSila cuba lagi kemudian. Ringkasan ralat: ',
            'vi': 'Câu trả lời cá nhân:\nDịch vụ AI tạm thời không thể kết nối.\n\nCâu trả lời chung:\nVui lòng thử lại sau. Tóm tắt lỗi: ',
            'ko': '개인 맞춤 답변:\nAI 서비스에 일시적으로 연결할 수 없습니다.\n\n일반 답변:\n나중에 다시 시도해 주세요. 오류 요약: ',
        }

        return {
            'reply': error_messages.get(language_code, error_messages['zh-hant']) + str(exc)[:180],
            'source': 'openai_error',
            'model': model,
        }

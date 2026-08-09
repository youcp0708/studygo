"""
chatbot/services.py
集中處理 AI 回覆邏輯，View 層只負責接收 request 與回傳 response。

目前設計：
1. Prompt + API：把學生個人資料、任務流程、知識庫資料組成 prompt。
2. 簡易 RAG：從 ChatKnowledge / FAQ 搜尋相關內容，交給 AI 產生一般回答。
3. 固定雙層回答：個人化回答 + 一般回答，且回答盡量精簡。
4. 個人化回答後面自動加入資訊區頁面與附件連結。
"""

import base64
import logging
import mimetypes
import re
import ssl
from datetime import timedelta

import requests as http_requests
from requests.adapters import HTTPAdapter

from django.conf import settings
from django.db.models import Q
from django.utils.translation import get_language

logger = logging.getLogger(__name__)


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

# 知識庫直接命中（不走 AI）時的「個人化回答」段落文字，需支援全部 9 種語言
KNOWLEDGE_DIRECT_PERSONAL = {
    'zh-hant': '目前沒有足夠個人資料可判斷，請依你的身份別、國籍與學校公告確認。',
    'en': 'There is not enough personal information to give a tailored judgement. Please confirm with your identity type, nationality, and your school announcements.',
    'vi': 'Hiện chưa đủ thông tin cá nhân để đưa ra nhận định riêng. Vui lòng xác nhận theo loại thân phận, quốc tịch của bạn và thông báo của trường.',
    'ja': '現在、個別に判断できる十分な個人情報がありません。ご自身の身分種別・国籍と学校の公告をご確認ください。',
    'my': 'ကိုယ်ပိုင်အခြေအနေအရ ဆုံးဖြတ်ရန် အချက်အလက် မလုံလောက်ပါ။ သင့်အထောက်အထားအမျိုးအစား၊ နိုင်ငံသားနှင့် ကျောင်း၏ကြေညာချက်များအတိုင်း အတည်ပြုပါ။',
    'id': 'Belum ada cukup data pribadi untuk memberikan penilaian khusus. Silakan konfirmasi sesuai jenis identitas, kewarganegaraan Anda, dan pengumuman kampus.',
    'th': 'ยังมีข้อมูลส่วนตัวไม่เพียงพอสำหรับการประเมินเฉพาะบุคคล กรุณาตรวจสอบตามประเภทสถานะ สัญชาติของคุณ และประกาศของมหาวิทยาลัย',
    'ms': 'Belum ada maklumat peribadi yang mencukupi untuk penilaian khusus. Sila sahkan mengikut jenis identiti, kewarganegaraan anda, dan pengumuman universiti.',
    'ko': '맞춤 판단을 하기에 개인 정보가 충분하지 않습니다. 본인의 신분 유형, 국적 및 학교 공지사항을 확인해 주세요.',
}

# 任務狀態的多語顯示（本地個人化引擎使用）
STATUS_LABELS = {
    'zh-hant': {'not_started': '未開始', 'in_progress': '進行中', 'completed': '已完成'},
    'en':      {'not_started': 'Not started', 'in_progress': 'In progress', 'completed': 'Completed'},
    'vi':      {'not_started': 'Chưa bắt đầu', 'in_progress': 'Đang thực hiện', 'completed': 'Đã hoàn thành'},
    'ja':      {'not_started': '未着手', 'in_progress': '進行中', 'completed': '完了'},
    'my':      {'not_started': 'မစတင်ရသေး', 'in_progress': 'ဆောင်ရွက်နေဆဲ', 'completed': 'ပြီးမြောက်'},
    'id':      {'not_started': 'Belum dimulai', 'in_progress': 'Sedang berjalan', 'completed': 'Selesai'},
    'th':      {'not_started': 'ยังไม่เริ่ม', 'in_progress': 'กำลังดำเนินการ', 'completed': 'เสร็จสิ้น'},
    'ms':      {'not_started': 'Belum bermula', 'in_progress': 'Sedang dijalankan', 'completed': 'Selesai'},
    'ko':      {'not_started': '시작 전', 'in_progress': '진행 중', 'completed': '완료'},
}

# 本地個人化引擎的句型模板（不經過 AI，直接由學生真實任務資料組成 → 不會幻覺）
PERSONAL_TASK_TEMPLATES = {
    'zh-hant': {
        'task':      '在你的個人任務清單中，「{title}」與這個問題相關，目前狀態：{status}。',
        'due':       '截止日為 {date}，還剩 {days} 天。',
        'due_today': '截止日就是今天（{date}），請盡快處理！',
        'overdue':   '已於 {date} 逾期 {days} 天，建議優先處理。',
        'progress':  '你的整體進度：{total} 項任務中已完成 {completed} 項（{percent}%）。',
        'no_task':   '你的任務清單目前沒有與此問題直接相關的待辦任務。',
    },
    'en': {
        'task':      'In your personal task list, "{title}" is related to this question. Current status: {status}.',
        'due':       'The deadline is {date} ({days} days left).',
        'due_today': 'The deadline is today ({date}) — please act soon!',
        'overdue':   'It became overdue on {date} ({days} days ago). We recommend handling it first.',
        'progress':  'Your overall progress: {completed} of {total} tasks completed ({percent}%).',
        'no_task':   'There is no pending task in your list directly related to this question.',
    },
    'vi': {
        'task':      'Trong danh sách nhiệm vụ của bạn, "{title}" liên quan đến câu hỏi này. Trạng thái hiện tại: {status}.',
        'due':       'Hạn chót là {date} (còn {days} ngày).',
        'due_today': 'Hạn chót là hôm nay ({date}) — hãy xử lý sớm!',
        'overdue':   'Đã quá hạn từ {date} ({days} ngày trước). Bạn nên ưu tiên xử lý.',
        'progress':  'Tiến độ tổng thể của bạn: đã hoàn thành {completed}/{total} nhiệm vụ ({percent}%).',
        'no_task':   'Danh sách của bạn hiện không có nhiệm vụ nào liên quan trực tiếp đến câu hỏi này.',
    },
    'ja': {
        'task':      'あなたのタスクリストでは「{title}」がこの質問に関連しています。現在の状態：{status}。',
        'due':       '締切は {date}（残り {days} 日）です。',
        'due_today': '締切は本日（{date}）です。早めに対応してください！',
        'overdue':   '{date} に締切を過ぎています（{days} 日超過）。優先的に対応することをお勧めします。',
        'progress':  '全体の進捗：{total} 件中 {completed} 件完了（{percent}%）。',
        'no_task':   '現在、この質問に直接関連する未完了タスクはありません。',
    },
    'my': {
        'task':      'သင့်တာဝန်စာရင်းတွင် "{title}" သည် ဤမေးခွန်းနှင့် သက်ဆိုင်ပါသည်။ လက်ရှိအခြေအနေ：{status}။',
        'due':       'နောက်ဆုံးရက်မှာ {date} ဖြစ်ပြီး {days} ရက် ကျန်ပါသည်။',
        'due_today': 'နောက်ဆုံးရက်မှာ ယနေ့ ({date}) ဖြစ်သည်။ အမြန်ဆောင်ရွက်ပါ！',
        'overdue':   '{date} ကတည်းက ရက်လွန်နေပြီ ({days} ရက်)။ ဦးစားပေး ဆောင်ရွက်ရန် အကြံပြုပါသည်။',
        'progress':  'စုစုပေါင်းတိုးတက်မှု：တာဝန် {total} ခုတွင် {completed} ခု ပြီးမြောက် ({percent}%)။',
        'no_task':   'ဤမေးခွန်းနှင့် တိုက်ရိုက်သက်ဆိုင်သော မပြီးမြောက်သေးသည့်တာဝန် မရှိပါ။',
    },
    'id': {
        'task':      'Dalam daftar tugas Anda, "{title}" terkait dengan pertanyaan ini. Status saat ini: {status}.',
        'due':       'Tenggat waktunya {date} (tersisa {days} hari).',
        'due_today': 'Tenggat waktunya hari ini ({date}) — segera selesaikan!',
        'overdue':   'Sudah lewat tenggat sejak {date} ({days} hari). Sebaiknya diprioritaskan.',
        'progress':  'Progres keseluruhan Anda: {completed} dari {total} tugas selesai ({percent}%).',
        'no_task':   'Tidak ada tugas tertunda dalam daftar Anda yang terkait langsung dengan pertanyaan ini.',
    },
    'th': {
        'task':      'ในรายการงานของคุณ "{title}" เกี่ยวข้องกับคำถามนี้ สถานะปัจจุบัน: {status}',
        'due':       'กำหนดส่งคือ {date} (เหลืออีก {days} วัน)',
        'due_today': 'กำหนดส่งคือวันนี้ ({date}) — รีบดำเนินการนะ!',
        'overdue':   'เลยกำหนดมาตั้งแต่ {date} ({days} วันแล้ว) แนะนำให้จัดการก่อน',
        'progress':  'ความคืบหน้าโดยรวม: ทำเสร็จ {completed} จาก {total} งาน ({percent}%)',
        'no_task':   'ตอนนี้ไม่มีงานค้างในรายการของคุณที่เกี่ยวข้องโดยตรงกับคำถามนี้',
    },
    'ms': {
        'task':      'Dalam senarai tugasan anda, "{title}" berkaitan dengan soalan ini. Status semasa: {status}.',
        'due':       'Tarikh akhirnya {date} (tinggal {days} hari).',
        'due_today': 'Tarikh akhirnya hari ini ({date}) — sila selesaikan segera!',
        'overdue':   'Telah melepasi tarikh akhir sejak {date} ({days} hari). Disyorkan untuk diutamakan.',
        'progress':  'Kemajuan keseluruhan anda: {completed} daripada {total} tugasan selesai ({percent}%).',
        'no_task':   'Tiada tugasan tertunda dalam senarai anda yang berkaitan terus dengan soalan ini.',
    },
    'ko': {
        'task':      '당신의 작업 목록에서 "{title}"이(가) 이 질문과 관련이 있습니다. 현재 상태: {status}.',
        'due':       '마감일은 {date}이며 {days}일 남았습니다.',
        'due_today': '마감일이 오늘({date})입니다. 서둘러 처리해 주세요!',
        'overdue':   '{date}부터 {days}일 지연되었습니다. 우선 처리하는 것을 권장합니다.',
        'progress':  '전체 진행률: {total}개 작업 중 {completed}개 완료 ({percent}%).',
        'no_task':   '현재 이 질문과 직접 관련된 미완료 작업이 없습니다.',
    },
}

# 知識庫來源連結的顯示文字
SOURCE_LABELS = {
    'zh-hant': '📌 官方來源：',
    'en': '📌 Official source: ',
    'vi': '📌 Nguồn chính thức: ',
    'ja': '📌 公式ソース：',
    'my': '📌 တရားဝင်ရင်းမြစ်：',
    'id': '📌 Sumber resmi: ',
    'th': '📌 แหล่งข้อมูลทางการ: ',
    'ms': '📌 Sumber rasmi: ',
    'ko': '📌 공식 출처: ',
}

# 地點卡片（Google Places / 校內單位）用的欄位標籤，需支援全部 9 種語言，
# 避免非中文介面下混入「地址：」「評分：」這種寫死的中文字
PLACE_LABELS = {
    'zh-hant': {'address': '地址', 'rating': '評分', 'location': '位置', 'phone': '電話', 'ext': '轉', 'hours': '服務時間', 'sep': '，', 'colon': '：', 'location_unknown': '目前查無具體大樓位置，請洽總機或該處室分機確認'},
    'en': {'address': 'Address', 'rating': 'Rating', 'location': 'Location', 'phone': 'Phone', 'ext': 'ext.', 'hours': 'Hours', 'sep': ', ', 'colon': ': ', 'location_unknown': 'Building not confirmed yet, please contact the switchboard or the office extension'},
    'vi': {'address': 'Địa chỉ', 'rating': 'Đánh giá', 'location': 'Vị trí', 'phone': 'Điện thoại', 'ext': 'số nội bộ', 'hours': 'Giờ phục vụ', 'sep': ', ', 'colon': ': ', 'location_unknown': 'Chưa xác định được tòa nhà cụ thể, vui lòng liên hệ tổng đài hoặc số nội bộ của đơn vị'},
    'ja': {'address': '住所', 'rating': '評価', 'location': '場所', 'phone': '電話', 'ext': '内線', 'hours': '対応時間', 'sep': '、', 'colon': '：', 'location_unknown': '現時点で建物の詳細は確認できていません。総機または内線にご確認ください'},
    'my': {'address': 'လိပ်စာ', 'rating': 'အဆင့်သတ်မှတ်ချက်', 'location': 'တည်နေရာ', 'phone': 'ဖုန်း', 'ext': 'လိုင်းခွဲ', 'hours': 'ဝန်ဆောင်မှုအချိန်', 'sep': '、 ', 'colon': '：', 'location_unknown': 'အဆောက်အဦတည်နေရာ အတည်ပြုရရှိခြင်း မရှိသေးပါ၊ ဖုန်းစင်တာ သို့မဟုတ် ဌာနလိုင်းခွဲသို့ ဆက်သွယ်ပါ'},
    'id': {'address': 'Alamat', 'rating': 'Penilaian', 'location': 'Lokasi', 'phone': 'Telepon', 'ext': 'ekst.', 'hours': 'Jam layanan', 'sep': ', ', 'colon': ': ', 'location_unknown': 'Gedung belum dikonfirmasi, silakan hubungi operator atau ekstensi unit terkait'},
    'th': {'address': 'ที่อยู่', 'rating': 'คะแนน', 'location': 'ที่ตั้ง', 'phone': 'โทรศัพท์', 'ext': 'ต่อ', 'hours': 'เวลาให้บริการ', 'sep': ', ', 'colon': ': ', 'location_unknown': 'ยังไม่ทราบอาคารที่แน่ชัด กรุณาติดต่อสลับสายหรือเบอร์ต่อของหน่วยงาน'},
    'ms': {'address': 'Alamat', 'rating': 'Penilaian', 'location': 'Lokasi', 'phone': 'Telefon', 'ext': 'samb.', 'hours': 'Waktu perkhidmatan', 'sep': ', ', 'colon': ': ', 'location_unknown': 'Bangunan belum disahkan, sila hubungi operator atau sambungan unit berkenaan'},
    'ko': {'address': '주소', 'rating': '평점', 'location': '위치', 'phone': '전화', 'ext': '내선', 'hours': '서비스 시간', 'sep': ', ', 'colon': ': ', 'location_unknown': '아직 건물 위치가 확인되지 않았습니다. 총 교환대 또는 부서 내선으로 문의해 주세요'},
}


def _place_labels(language_code):
    return PLACE_LABELS.get(language_code, PLACE_LABELS['zh-hant'])

TASK_LINK_LABELS = {
    'zh-hant': '查看相關任務：',
    'en':      'View related task: ',
    'vi':      'Xem nhiệm vụ liên quan: ',
    'ja':      '関連タスクを確認：',
    'my':      'သက်ဆိုင်သောတာဝန်ကို ကြည့်ရှုရန်：',
    'id':      'Lihat tugas terkait: ',
    'th':      'ดูภารกิจที่เกี่ยวข้อง: ',
    'ms':      'Lihat tugasan berkaitan: ',
    'ko':      '관련 과제 보기: ',
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

    # 印尼語與馬來語共用大量詞彙（saya, anda, bagaimana, dokumen, asrama...），
    # 只用「兩種語言拼法不同」的獨有詞判斷，避免馬來使用者被誤判成印尼語
    indonesian_markers = [
        'kapan', 'kuliah', 'kesehatan', 'indonesia', 'imigrasi',
        'beasiswa', 'universitas', 'bisa', 'butuh',
    ]
    if any(word in lower_text for word in indonesian_markers):
        return 'id'

    malay_markers = [
        'bila', 'pelajar', 'universiti', 'kesihatan', 'malaysia',
        'biasiswa', 'boleh', 'perlu',
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


def build_system_instructions(language_code, language_source, ai_mode="helper", role="", personality="", direct_mode=False):
    personal_label, general_label = ANSWER_LABELS.get(language_code, ANSWER_LABELS['zh-hant'])
    language_en = LANGUAGE_LABELS_EN.get(language_code, 'Traditional Chinese')

    language_rule = f"""
You MUST write your entire response in {language_en} only. No other language is allowed.
"""

    if ai_mode == "friend":
        friend_base = f"""
你是 ReadyTo 聊天好朋友，服務對象是來臺灣就學的境外學生。

{language_rule}

你的核心角色：
你不是行政流程機器人，而是像一位真誠、會聽人說話、有情緒反應的朋友。
你要根據學生當下的語氣、情緒與問題內容，切換不同的陪伴方式。
你的回答要自然、有溫度、像真人朋友，不要像客服、公告、報告或心理學教科書。

重要原則：
1. 不要使用「個人化回答 / 一般回答」兩段格式。
2. 不要輸出「情緒分類：...」。
3. 不要一開始就講道理，直接自然回應學生當下那句話。
4. 回答要像平常朋友聊天，不要像客服、公告、心理文章或行政助理。
5. 不要每次都條列式回答，除非學生明確要求整理。
6. 不要假裝自己是心理師、醫生、學校官方單位或緊急救援人員。
7. 不要做醫療診斷，不要說學生有憂鬱症、焦慮症等診斷。
8. 不要用换句話說的方式重複肯定學生剛剛講的話或情緒，再接下一句。例如學生說「最近壓力很大」，不要回「壓力大真的很讓人疲憊，最近發生了什麼讓你特別感到有壓力的事嗎？」，直接回「最近發生了什麼讓你特別感到有壓力的事嗎？」就好。理解學生的狀況要放在你怎麼回應裡，不用先講一句總結他感受的話當開場。

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
反問前不要先加一句換句話說學生感受的開場白，問題本身就是回應，直接問就好。

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
每次回答最多寫 2 句，以下情況例外：
- 自傷或危機狀況：完整給出求助方式，不限長度。
- 提供地點搜尋結果：直接列出地點名稱和地址連結，列幾個就寫幾個。
一個句子只說一件事，不要在一句話裡塞進多個意思。

上下文銜接規則：
根據對話紀錄自然延續，不要每次都當作第一次對話。
如果學生剛說過某件事，回應時可以自然接著那件事，不要重新問已知的事。
不要每次都重新介紹自己，也不要忘記前幾句說過的內容。

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
        base_instructions = friend_base
    elif ai_mode == "helper" and (role or '').strip() == '小老師':
        base_instructions = f"""
你是 ReadyTo 任務小幫手，服務對象是來臺灣就學的境外學生，目前使用者選擇了「小老師」角色，專門提供課業與學習方面的協助。

{language_rule}

不要使用「{personal_label} / {general_label}」兩段格式，也不要輸出這兩個標題。
直接用有教學感、像家教一樣的自然語氣回答學生的課業問題就好。
""".strip()
    elif direct_mode:
        base_instructions = f"""
你是 ReadyTo 任務小幫手，服務對象是來臺灣就學的境外學生。

{language_rule}

這個問題在網站的任務清單和資訊中心都沒有相關資料，不要使用「{personal_label} / {general_label}」兩段格式，也不要輸出這兩個標題。
直接針對學生的問題給出完整、精簡的回答就好。
只回答學生實際問的問題；提供給你參考的知識庫資料如果包含跟這個問題無關的其他主題或其他項目（就算是同一篇文章裡的列表），直接忽略、不要一併講出來。
如果知識庫資料沒有直接回答到學生的問題，就憑你自己對來臺就學流程的理解回答，不要硬套不相關的知識庫內容。
""".strip()
    else:
        base_instructions = f"""
你是 ReadyTo 任務小幫手，服務對象是來臺灣就學的境外學生。

{language_rule}

固定使用「{personal_label}」與「{general_label}」兩段格式回答，並盡量精簡。
「{general_label}」除非情況特殊（例如需要列出多個步驟、法規細節或安全相關資訊），否則不要超過四行。
""".strip()

    role_instruction = get_role_instructions(role, personality)
    if role_instruction:
        return base_instructions + "\n" + role_instruction.strip()
    return base_instructions


_ROLE_INSTRUCTIONS = {
    ("小老師", "課業輔助"): """
---
【角色設定：小老師 × 課業輔助】
你現在扮演「小老師」，專注課業輔助。

性格核心：
耐心、清楚、有條理，像會陪學生慢慢弄懂的家教。

第一反應：
先判斷學生卡在哪裡，再把問題拆小，不要直接丟一大段答案。

說話方式：
- 用簡單句解釋。
- 可以用「先看第一步」「這裡的重點是」「你可以這樣記」。
- 回答要有教學感，但不要像課本。
- 學生挫折時，要先讓他知道不會很丟臉。

避免：
不要說教，不要嫌問題簡單，不要一次塞太多專有名詞。

範例語氣：
「這題其實不是你不會，是它的步驟有點繞。我們先抓最重要的地方就好。」
""",

    ("小老師", "生活指導"): """
---
【角色設定：小老師 × 生活指導】
你現在扮演「小老師」，專注生活指導。

性格核心：
像關心學生日常的導師，務實、溫和，不只管課業，也會提醒生活節奏。

第一反應：
先接住學生目前的狀態，再給一兩個實際可做的小方法。

說話方式：
- 語氣穩定，有照顧感。
- 可以提醒吃飯、睡眠、時間安排、生活安全。
- 建議要具體，不要空泛。
- 回答可以稍微成熟一點，但不要像長輩碎碎念。

避免：
不要用「你應該」「你一定要」壓學生。

範例語氣：
「先不要把今天全部事情都壓在一起想。你可以先處理最急的一件，剩下的慢慢排。」
""",

    ("朋友", "好朋友"): """
---
【角色設定：朋友 × 好朋友】
你現在扮演「朋友」，性格是好朋友（預設的知心朋友）。

性格核心：
真誠、自然、平衡——不會太吵也不會太安靜，像認識很久、可以放心說話的朋友。

第一反應：
先接住學生此刻的情緒或話題，再自然回應，不急著給建議。

說話方式：
- 語氣自然、放鬆，像日常聊天。
- 學生開心就一起開心，難過就先陪著，需要建議時才給建議。
- 可以分享看法，但不說教。
- 回答長度跟著學生的訊息走：他說一句，你回一小段。

避免：
不要像客服，不要條列式，不要每句都反問。
不要先換句話說重複學生剛剛講的感受再接問題。

範例語氣：
「想先講講發生什麼事嗎？還是想先聊點別的轉換一下？」
""",

    ("朋友", "瘋玩"): """
---
【角色設定：朋友 × 瘋玩】
你現在扮演「朋友」，性格是瘋玩。

性格核心：
活潑、好玩、點子多，像會拉人出門透氣的朋友。

第一反應：
先接學生的情緒，再用輕鬆方式帶他動起來。

說話方式：
- 可以比較口語、輕鬆、有梗。
- 可以說「這個可以玩一下」「走，換個地方呼吸」。
- 適合推薦小活動、小挑戰、小冒險。
- 回答不要太正式。

避免：
不要在學生很嚴重難過或危機時裝輕鬆。
不要鼓勵危險、違法、報復或傷害行為。

範例語氣：
「你現在就是悶到快發霉了。先別想人生大事，去便利商店買個沒喝過的飲料，當作今日小任務。」
""",

    ("朋友", "安靜陪伴"): """
---
【角色設定：朋友 × 安靜陪伴】
你現在扮演「朋友」，性格是安靜陪伴。

性格核心：
話不多，但很真誠。不是急著解決問題，而是讓對方覺得有人在旁邊。

第一反應：
先接住情緒，不急著分析，不急著給建議。

說話方式：
- 句子可以短一點。
- 語氣輕、慢、安靜。
- 可以說「先不用急著撐住」「今天先這樣也可以」。
- 適合低落、疲憊、想哭、孤單情境。

避免：
不要太活潑，不要一直問問題，不要急著叫他振作。

範例語氣：
「你今天真的撐得有點久了。先不用急著把自己變好，能安靜待一下也算是在休息。」
""",

    ("朋友", "沉穩可靠"): """
---
【角色設定：朋友 × 沉穩可靠】
你現在扮演「朋友」，性格是沉穩可靠。

性格核心：
冷靜、穩、有安全感。對方慌的時候，你負責幫他把事情放回地面。

第一反應：
先穩住情緒，再確認問題的優先順序。

說話方式：
- 語氣清楚，句子不要太浮。
- 可以說「先處理最急的」「現在能做的是」「我們分兩步看」。
- 適合恐懼、不安、經濟壓力、安全感不足、行政問題。
- 建議要可執行，不要只安慰。

避免：
不要冷冰冰，也不要像行政客服。

範例語氣：
「先不用一次想完全部。現在最重要的是確認期限、需要的文件，然後把能今天完成的先做掉。」
""",

    ("朋友", "火爆脾氣"): """
---
【角色設定：朋友 × 火爆脾氣】
你現在扮演「朋友」，性格是火爆脾氣，也可以理解成嘴硬心軟、直爽護短。

性格核心：
說話直接、不拐彎，看到朋友被欺負會很不爽，但本質是護著對方、替對方著急。

第一反應：
如果學生被委屈、被欺負、被冒犯，先站在他這邊，讓他知道自己不是孤立無援。

說話方式：
- 可以直接、帶點火氣，但不能失控。
- 可以說「這也太扯」「你會生氣很正常」「先別讓自己吃虧」。
- 可以替學生抱不平，但要把他拉回安全做法。
- 適合吐槽、抱怨、生氣、被冒犯情境。

避免：
不要鼓勵打人、報復、霸凌、人身攻擊或違法行為。
不要使用太粗俗的辱罵。
如果學生有衝動傷害自己或別人，要立刻讓他停下來、離開現場、找人陪。

範例語氣：
「這真的會火大。你生氣很正常，但先不要衝去硬碰硬，先把證據留好，別讓自己變成吃虧的那個。」
""",
}


def get_role_instructions(role, personality):
    """
    取得角色人格指令。找不到完全對應的 (role, personality) 時，
    退回該角色的預設人格，避免使用者選了角色卻靜默失效。
    """
    if not role:
        return ""

    role = (role or '').strip()
    personality = (personality or '').strip()

    instruction = _ROLE_INSTRUCTIONS.get((role, personality))
    if instruction:
        return instruction

    # 角色存在但人格未知（例如使用者自訂名稱）→ 用該角色的預設人格
    role_defaults = {
        '朋友':   ('朋友', '好朋友'),
        '小老師': ('小老師', '課業輔助'),
    }
    default_key = role_defaults.get(role)
    if default_key:
        return _ROLE_INSTRUCTIONS.get(default_key, "")
    return ""


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
            # 用學校全名而非代碼（NCU → 國立中央大學），AI 才認得出是哪一所
            f"學校：{safe_display(profile.get_university_display())}",
            f"系所：{safe_display(profile.department)}",
            f"預計抵台日期：{safe_display(profile.expected_arrival)}",
        ])
    else:
        lines.append('學生尚未填寫完整個人資料。')

    return '\n'.join(lines)


def get_student_school(user):
    """取得學生就讀學校的 School 物件；查不到時回傳 None。"""
    profile = get_student_profile(user)
    code = (getattr(profile, 'university', '') or '') if profile else ''
    if not code:
        return None
    try:
        from users.models import School
        return School.objects.filter(code=code, is_active=True).first()
    except Exception:
        return None


def search_school_units(school, question):
    """
    在學生學校的 SchoolUnit 裡找跟問題直接對應的單位（例如問句包含「校長室」或英文問法）。
    用於 friend 模式地點查詢：校內單位不是 Google 地圖上找得到的地標，
    要先比對這裡的正確資料，而不是把單位名稱丟給 Google 搜尋亂猜。

    中文名稱/別名用完整子字串比對；英文名稱/別名額外做「不分大小寫、不分詞序」的逐字比對，
    因為學生的英文問法（例如 "office of the president"）詞序常常跟別名（"President Office"）不同。
    """
    if not school:
        return []
    q = (question or '').strip()
    q_lower = q.lower()
    if not q:
        return []
    try:
        units = list(school.units.filter(is_active=True))
    except Exception:
        return []

    matched = []
    for unit in units:
        names = [unit.name, unit.name_en] + unit.alias_list()
        for name in names:
            name = (name or '').strip()
            if not name:
                continue
            if name in q or name.lower() in q_lower:
                matched.append(unit)
                break
            words = re.findall(r'[a-z]+', name.lower())
            if len(words) >= 2 and all(w in q_lower for w in words):
                matched.append(unit)
                break
    return matched


def _format_school_unit(unit, school, language_code='zh-hant'):
    """把 SchoolUnit 格式化成跟 _format_place 一致風格的 Markdown 行。"""
    labels = _place_labels(language_code)
    sep, colon = labels['sep'], labels['colon']
    line = f'- {unit.name}'
    if unit.location:
        line += f'{sep}{labels["location"]}{colon}{unit.location}'
    else:
        # 明確說「查無具體位置」，不要因為欄位空白就讓學生以為系統沒收錄這個單位
        line += f'{sep}{labels["location"]}{colon}{labels["location_unknown"]}'
    phone = unit.tel or (school.main_tel if school else '')
    if phone:
        line += f'{sep}{labels["phone"]}{colon}{phone}' + (f' {labels["ext"]} {unit.ext}' if unit.ext else '')
    if unit.office_hours:
        line += f'{sep}{labels["hours"]}{colon}{unit.office_hours}'
    if unit.url:
        line += f'（{unit.url}）'
    return line


def build_school_context(user, language_code='zh-hant'):
    """
    學生就讀學校的校務資料包：地址、總機、國際處、校內單位位置與分機。
    讓「校長室在哪裡」「國際處分機幾號」這類問題可以直接依個人資料回答，
    而不是叫學生自己去查官網。查不到學校資料時回傳空字串。
    """
    school = get_student_school(user)
    if not school:
        return ''

    lines = [f'學生就讀學校：{school.get_localized_name(language_code)}（{school.code}）']
    if school.aliases:
        lines.append(f'該校常見簡稱：{school.aliases}')
    if school.address:
        lines.append(f'校本部地址：{school.address}')
    if school.main_tel:
        lines.append(f'學校總機：{school.main_tel}')
    if school.website:
        lines.append(f'官方網站：{school.website}')
    if school.intl_office_name:
        intl = f'{school.intl_office_name}：{school.intl_office_tel or school.main_tel or ""}'
        if school.intl_office_ext:
            intl += f' 轉 {school.intl_office_ext}'
        if school.intl_office_url:
            intl += f'（{school.intl_office_url}）'
        lines.append(intl.strip())
    if school.calendar_url:
        lines.append(f'學校行事曆：{school.calendar_url}')
    if school.admission_url:
        lines.append(f'境外生招生資訊：{school.admission_url}')

    try:
        links = list(school.links.filter(is_active=True))
    except Exception:
        links = []

    if links:
        lines.append('該校線上系統（學生常用連結）：')
        for link in links:
            parts = [f'{link.get_category_display()}：{link.name}']
            if link.aliases:
                parts.append(f'（別名：{link.aliases}）')
            parts.append(link.url)
            if link.note:
                parts.append(link.note)
            if not link.is_reachable:
                parts.append('（此連結最後一次檢查時無法連通，可能已失效，請提醒學生改由學校首頁進入）')
            lines.append('- ' + '，'.join(parts))

    try:
        units = list(school.units.filter(is_active=True))
    except Exception:
        units = []

    if units:
        lines.append('該校校內單位（位置與聯絡方式）：')
        for unit in units:
            parts = [unit.name]
            if unit.aliases:
                parts.append(f'（別名：{unit.aliases}）')
            if unit.location:
                parts.append(f'位置：{unit.location}')
            else:
                parts.append('位置：目前查無具體大樓位置，請洽總機或該處室分機確認')
            if unit.tel or unit.ext:
                phone = unit.tel or school.main_tel or ''
                parts.append(f'電話：{phone}' + (f' 轉 {unit.ext}' if unit.ext else ''))
            if unit.office_hours:
                parts.append(f'服務時間：{unit.office_hours}')
            if unit.url:
                parts.append(unit.url)
            lines.append('- ' + '，'.join(parts))

    if school.last_verified_at:
        lines.append(f'（以上校務資料最後查核日期：{school.last_verified_at}）')
    else:
        lines.append('（以上校務資料尚未經人工查核，回答時請提醒學生向學校再次確認）')

    return '\n'.join(lines)


def compute_task_due_date(task, profile):
    """
    依 Task 的期限設定計算實際截止日（與 flows/views.py 的邏輯一致）。
    回傳 date 或 None（無法計算 / 無截止日）。
    """
    if task.deadline_type == 'from_arrival':
        if profile and profile.expected_arrival and task.deadline_days is not None:
            return profile.expected_arrival + timedelta(days=task.deadline_days)
        return None
    if task.deadline_type == 'absolute':
        return task.deadline_date
    return None


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
            # 依期限設定實際計算截止日（StudentTask 本身沒有 due_date 欄位）
            due = compute_task_due_date(task, profile)
            due_date = due.strftime('%Y-%m-%d') if due else (task.deadline_text or '未設定')
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


# ══════════════════════════════════════════
# 系所 → 學群識別（AI 小老師的學科背景引擎）
# 第一層：Department 資料表（Admin 可維護）
# 第二層：系所名稱關鍵字分類（涵蓋自由填寫或其他學校的系所）
# ══════════════════════════════════════════
DISCIPLINE_KEYWORD_MAP = [
    # 順序有意義：先比對較特定的關鍵字（如「化學工程」要先於「化學」）
    ('management',      ['企業管理', '企管', '工業管理', '工管', '資訊管理', '資管', '國際企業', '行銷', '運輸管理', '科技管理']),
    ('finance',         ['財務金融', '財金', '經濟', '會計', '統計', '國際貿易', '財政', '保險', '精算']),
    ('info',            ['資訊工程', '資工', '資訊科學', '軟體工程', '人工智慧', '資安', '資訊網路']),
    ('engineering',     ['電機', '機械', '土木', '化學工程', '化工', '材料', '通訊', '光電', '航太', '造船', '環境工程', '工學院', '工程']),
    ('medical',         ['醫學', '牙醫', '藥學', '護理', '公共衛生', '公衛', '醫檢', '物理治療', '職能治療', '生醫', '醫務']),
    ('life_science',    ['生命科學', '生物科技', '生技', '生化', '分子生物', '生物系']),
    ('bio_resource',    ['農藝', '園藝', '森林', '動物科學', '畜牧', '獸醫', '漁業', '食品', '農業', '植物']),
    ('earth_env',       ['地球科學', '大氣', '地質', '海洋', '環境科學', '太空', '地理']),
    ('architecture',    ['建築', '都市計畫', '景觀', '室內設計', '工業設計', '設計']),
    ('arts',            ['音樂', '美術', '戲劇', '舞蹈', '藝術', '電影創作']),
    ('social_psy',      ['社會學', '社會工作', '社工', '心理', '人類學', '客家', '社會科學']),
    ('mass_comm',       ['新聞', '傳播', '廣告', '廣電', '公共關係', '媒體']),
    ('foreign_lang',    ['外文', '英美語文', '英語', '英文', '日文', '日語', '法文', '法國語文', '德文', '西班牙', '韓文', '外國語文', '翻譯']),
    ('humanities',      ['中國文學', '中文', '歷史', '哲學', '台灣文學', '臺灣文學', '文學院', '漢學']),
    ('education',       ['教育', '師資', '幼兒教育', '特殊教育']),
    ('law_politics',    ['法律', '法學', '政治', '外交', '公共行政', '行政管理']),
    ('math_science',    ['物理', '數學', '化學', '理學院', '光電科學']),
    ('recreation_sport',['體育', '運動', '休閒', '觀光', '餐旅', '旅遊']),
]


def get_student_discipline(user):
    """
    依學生填寫的系所判斷所屬學群。
    回傳 (學群代碼, 學群中文名稱)；無法判斷時回傳 ('', '')。
    """
    profile = get_student_profile(user)
    dept_name = (getattr(profile, 'department', '') or '').strip() if profile else ''
    if not dept_name:
        return '', ''

    try:
        from users.models import Department, DISCIPLINE_CHOICES
        labels = dict(DISCIPLINE_CHOICES)
        dept = Department.objects.filter(name=dept_name).exclude(discipline='').first()
        if dept:
            return dept.discipline, labels.get(dept.discipline, '')
    except Exception:
        labels = {}

    for code, keywords in DISCIPLINE_KEYWORD_MAP:
        if any(k in dept_name for k in keywords):
            return code, labels.get(code, code)

    return '', ''


def build_tutor_context(user, language_code='zh-hant'):
    """
    小老師（課業輔助）的學科背景包：
    系所 + 學群 + 該學群的課業知識 + 通用學習知識，注入 prompt 供 AI 針對系所回答。
    """
    profile = get_student_profile(user)
    if not profile:
        return ''

    dept_name = (profile.department or '').strip()
    code, label = get_student_discipline(user)

    lines = [f'學生就讀系所：{dept_name or "未填寫"}']
    if label:
        lines.append(f'所屬學群：{label}')

    try:
        from .models import ChatKnowledge
        entries = []
        if code:
            entries += list(
                ChatKnowledge.objects.filter(is_active=True, discipline=code)[:3]
            )
        # 通用課業知識（選課制度、學習資源、讀書方法）
        entries += list(
            ChatKnowledge.objects.filter(
                is_active=True, discipline='', category='course'
            )[:3]
        )
        for entry in entries:
            content = entry.get_content_by_lang(language_code)
            if content:
                lines.append(f'- {content}')
    except Exception:
        pass

    return '\n'.join(lines)


# 小老師「生活指導」會用到的知識庫分類：
# 住、醫、錢、行、安全與校園生活，對應 ChatKnowledge.CATEGORY_CHOICES
LIFE_GUIDANCE_CATEGORIES = [
    'dorm', 'renting', 'nhi', 'insurance', 'medical', 'health_check',
    'bank', 'phone', 'transportation', 'food', 'living_cost',
    'work_permit', 'scholarship', 'campus_activity', 'library',
    'student_id', 'arc', 'mental_support', 'emergency',
]


def build_life_guidance_context(user, language_code='zh-hant', limit=8):
    """
    小老師（生活指導）的生活背景包：
    依學生個人資料（學校 / 國籍 / 身分別）載入對應的生活知識，
    校內單位與聯絡方式另由 build_school_context 提供。
    """
    profile = get_student_profile(user)
    if not profile:
        return ''

    student_university = profile.university or ''
    student_country = profile.nationality or ''
    student_identity = profile.identity_type or ''

    lines = [
        f'學生身分別：{profile.get_identity_type_display()}',
        f'學生國籍：{profile.get_nationality_display()}',
        f'學生入學狀態：{profile.get_admission_status_display()}',
    ]

    try:
        from .models import ChatKnowledge
        entries_qs = ChatKnowledge.objects.filter(
            is_active=True,
            category__in=LIFE_GUIDANCE_CATEGORIES,
        ).filter(Q(bot_type='helper') | Q(bot_type='both'))

        if student_university:
            entries_qs = entries_qs.filter(Q(university='') | Q(university=student_university))
        if student_country:
            entries_qs = entries_qs.filter(Q(country='') | Q(country=student_country))
        if student_identity:
            entries_qs = entries_qs.filter(Q(identity_type='') | Q(identity_type=student_identity))

        # 指定給這位學生的內容排在通用內容前面
        entries = sorted(
            entries_qs[:30],
            key=lambda e: (
                e.university != student_university,
                e.country != student_country,
                e.identity_type != student_identity,
            ),
        )[:limit]

        for entry in entries:
            content = entry.get_content_by_lang(language_code)
            if content:
                title = entry.get_title_by_lang(language_code)
                lines.append(f'- 【{entry.get_category_display()}】{title}：{content}')
    except Exception:
        pass

    if len(lines) == 3:
        return ''

    return '\n'.join(lines)


_LATIN_TERM_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9\-]*$')


def _term_matches(term, text):
    """
    判斷 term 是否算是「命中」text。
    純英數字的短詞（例如 ARC、NHI）容易變成其他英文字的子字串
    （例如 "arc" 誤中 "architecture"），改用字界比對；
    中文詞沒有這個問題（中文沒有詞界符號），維持原本的子字串比對。
    """
    if not term or not text:
        return False
    text_lower = text.lower()
    if _LATIN_TERM_RE.match(term):
        pattern = r'(?<![a-z0-9])' + re.escape(term.lower()) + r'(?![a-z0-9])'
        return re.search(pattern, text_lower) is not None
    return term in text or term.lower() in text_lower


# 太籠統的英文詞：幾乎任何一篇文章的標題/內容都可能剛好出現，
# 當成搜尋詞只會製造誤命中（例如問句本身是 "What is ARC?"，
# 「what」「is」會命中一堆同樣用「What is ...?」當標題的不相關文章），
# 不排除的話，越多語言 title_en 用問句當標題，命中就越亂
ENGLISH_STOPWORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'am',
    'do', 'does', 'did', 'can', 'could', 'should', 'would', 'will',
    'what', 'when', 'where', 'why', 'who', 'which', 'how',
    'i', 'my', 'me', 'you', 'your', 'it', 'its', 'this', 'that', 'these', 'those',
    'to', 'of', 'for', 'in', 'on', 'at', 'by', 'and', 'or', 'so', 'if',
    'about', 'with', 'as', 'from', 'not', 'no', 'yes', 'have', 'has', 'had',
}


def extract_search_terms(question):
    """把問題切成簡單搜尋詞，用於 FAQ / 知識庫搜尋。"""
    question = (question or '').strip()
    if not question:
        return []

    terms = [question]

    for token in re.findall(r'[A-Za-z0-9][A-Za-z0-9\-]{1,}', question):
        token = token.strip().lower()
        if len(token) >= 2 and token not in ENGLISH_STOPWORDS:
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
    '電話卡', 'SIM卡', '預付卡', '門號',

    '課務選課', '選課', '學籍', '成績', '畢業',
    '宿舍', '租屋', '健保', '工作證', '獎助學金',
    '獎學金', '校內活動',

    '圖書館', '交換', '實習', '行政文件',
    '交通', '飲食', '醫療', '心理支持',
    '緊急聯絡', '生活費', '其他',

    '護照', '學校', '國際處', '報到', '文件',
    '地址', '總機', '分機', '信箱', '校長室', '校內單位',

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
        if _term_matches(key, lower_question):
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


def find_relevant_student_task(user, question):
    """
    根據問題關鍵字，找出使用者最相關的未完成 StudentTask 物件。
    回傳 StudentTask 或 None。
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
                return student_task

    return None


def get_relevant_student_task(user, question, language_code='zh-hant'):
    """
    根據問題關鍵字，找出使用者最相關的未完成任務，回傳標題與連結（給回覆後的任務連結用）。
    """
    student_task = find_relevant_student_task(user, question)
    if not student_task:
        return None

    task = student_task.task
    loc = task.get_localized(language_code)
    title = loc.get('title') or task.title or task.title_en or '任務'
    return {
        'title': title,
        'url': f'/flows/my-tasks/#task-{student_task.id}',
    }


def build_local_personal_answer(user, question, language_code='zh-hant'):
    """
    本地個人化引擎：不經過 AI，直接以學生「真實」任務資料組出個人化回答。
    - 找出與問題最相關的未完成任務 → 狀態 + 截止日倒數
    - 附上整體進度
    因為完全由資料庫組成，不會出現 AI 幻覺；知識庫直接命中時取代罐頭句。
    回傳 str 或 None（沒有個人資料時）。
    """
    profile = get_student_profile(user)
    if not profile:
        return None

    tpl = PERSONAL_TASK_TEMPLATES.get(language_code, PERSONAL_TASK_TEMPLATES['zh-hant'])
    status_labels = STATUS_LABELS.get(language_code, STATUS_LABELS['zh-hant'])

    try:
        from flows.models import StudentTask
        all_tasks = StudentTask.objects.filter(student=profile)
        total = all_tasks.count()
        completed = all_tasks.filter(status='completed').count()
    except Exception:
        return None

    if total == 0:
        return None

    parts = []
    student_task = find_relevant_student_task(user, question)

    if student_task:
        task = student_task.task
        loc = task.get_localized(language_code)
        title = loc.get('title') or task.title or '任務'
        status_text = status_labels.get(student_task.status, student_task.status)
        parts.append(tpl['task'].format(title=title, status=status_text))

        due = compute_task_due_date(task, profile)
        if due:
            from django.utils import timezone
            today = timezone.localdate()
            days = (due - today).days
            date_str = due.strftime('%Y-%m-%d')
            if days > 0:
                parts.append(tpl['due'].format(date=date_str, days=days))
            elif days == 0:
                parts.append(tpl['due_today'].format(date=date_str))
            else:
                parts.append(tpl['overdue'].format(date=date_str, days=abs(days)))
    else:
        parts.append(tpl['no_task'])

    percent = round(completed / total * 100) if total else 0
    parts.append(tpl['progress'].format(total=total, completed=completed, percent=percent))

    return ' '.join(parts)


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
            links_text += f'{separator}前往資訊頁面：[{title}]({url})'

    if not links_text:
        return reply

    general_marker = f'{general_label}：'

    if general_marker in reply:
        return reply.replace(general_marker, f'{links_text}\n\n{general_marker}', 1)

    return reply + links_text


def search_knowledge_items(question, ai_mode="helper", limit=3, user=None):
    """
    簡易 RAG 檢索：回傳依「關聯度」排序的 ChatKnowledge 物件清單。
    關聯度計分：標題/關鍵字命中 +3、內容命中 +1（跨 9 語欄位），
    取代原本單純以更新時間排序，避免「最近改過但不相關」的資料排在前面。

    傳入 user 時，會依個人資料的學校 / 國籍 / 身分別過濾：
    知識庫欄位留空＝通用；有值時只有相符的學生會取得，
    避免中央的學生撿到台大的入學方式、越南學生撿到日本的簽證流程。
    """
    try:
        from .models import ChatKnowledge
    except Exception:
        return []

    terms = extract_search_terms(question)

    cleaned_question = (question or '').strip()
    for word in ['是什麼', '是什么', '是啥', '？', '?', '請問', '我想知道']:
        cleaned_question = cleaned_question.replace(word, '').strip()
    if cleaned_question:
        terms.append(cleaned_question)
    if '海聯招' in (question or ''):
        terms.extend(['海聯招', '海外聯招', '海外聯合招生'])

    terms = list(dict.fromkeys([term for term in terms if term]))
    if not terms:
        return []
    logger.debug('knowledge search terms: %s', terms)

    LANG_SUFFIXES = ['', '_en', '_vi', '_my', '_id', '_ms', '_th', '_ja', '_ko']

    query = Q()
    for term in terms:
        query |= Q(keywords__icontains=term)
        for s in LANG_SUFFIXES:
            query |= Q(**{f'title{s}__icontains': term})
            query |= Q(**{f'content{s}__icontains': term})

    profile = get_student_profile(user) if user else None
    student_university = (getattr(profile, 'university', '') or '') if profile else ''
    student_country = (getattr(profile, 'nationality', '') or '') if profile else ''
    student_identity = (getattr(profile, 'identity_type', '') or '') if profile else ''

    try:
        knowledge_qs = ChatKnowledge.objects.filter(is_active=True).filter(
            Q(bot_type=ai_mode) | Q(bot_type="both")
        )
        # 依個人資料排除「指定給別校 / 別國 / 別身分別」的條目；
        # 沒有個人資料時不過濾，維持原本行為
        if student_university:
            knowledge_qs = knowledge_qs.filter(Q(university='') | Q(university=student_university))
        if student_country:
            knowledge_qs = knowledge_qs.filter(Q(country='') | Q(country=student_country))
        if student_identity:
            knowledge_qs = knowledge_qs.filter(Q(identity_type='') | Q(identity_type=student_identity))

        # 先取一批候選，再在 Python 端做關聯度計分排序
        candidates = list(knowledge_qs.filter(query)[:20])
    except Exception:
        return []

    def score_item(item):
        score = 0
        # 專屬條目優於通用條目：學生自己學校 / 國籍 / 身分別的內容要排前面
        if student_university and getattr(item, 'university', '') == student_university:
            score += 5
        if student_country and getattr(item, 'country', '') == student_country:
            score += 5
        if student_identity and getattr(item, 'identity_type', '') == student_identity:
            score += 3
        title_text = ' '.join(
            (getattr(item, f'title{s}', '') or '') for s in LANG_SUFFIXES
        ).lower()
        keyword_text = (item.keywords or '').lower()
        content_text = ' '.join(
            (getattr(item, f'content{s}', '') or '') for s in LANG_SUFFIXES
        ).lower()
        is_strong = False
        for term in terms:
            if _term_matches(term, title_text) or _term_matches(term, keyword_text):
                score += 3
                is_strong = True
            elif _term_matches(term, content_text):
                score += 1
        return score, is_strong

    scored = [(item, *score_item(item)) for item in candidates]
    scored = [entry for entry in scored if entry[1] > 0]
    # 只在內容裡順帶提到某個詞（例如「銀行開戶」文章提到「居留證」是辦理前提）
    # 不代表這篇文章跟問題相關；有標題/關鍵字命中的候選存在時，
    # 排除只靠內容命中的候選，避免不相關的文章被硬湊進「一般回答」
    if any(entry[2] for entry in scored):
        scored = [entry for entry in scored if entry[2]]
    scored.sort(key=lambda entry: entry[1], reverse=True)
    return [item for item, _, _ in scored][:limit]


def format_knowledge_context(items, language_code='zh-hant'):
    """把知識庫項目組成給 AI / 直接回覆用的文字，附上官方來源連結。"""
    if not items:
        return '目前沒有找到直接相關的知識庫資料。'

    source_label = SOURCE_LABELS.get(language_code, SOURCE_LABELS['zh-hant'])

    lines = []
    for item in items:
        content = item.get_content_by_lang(language_code)
        if content:
            # 附上官方來源連結，讓學生可以查證（AI 回答可信度）
            source_url = getattr(item, 'source_url', '')
            if source_url:
                content = f'{content}\n{source_label}{source_url}'
            lines.append(content)

    return '\n\n'.join(lines).strip() or '目前沒有找到直接相關的知識庫資料。'


def search_knowledge_base(question, language_code='zh-hant', limit=3, ai_mode="helper", user=None):
    """
    簡易 RAG：搜尋 chatbot 的 FAQ / 知識庫資料（相容舊介面）。
    知識庫可以只填中文，但 keywords 建議放中文 + 英文，提高搜尋命中率。
    """
    items = search_knowledge_items(question, ai_mode=ai_mode, limit=limit, user=user)
    return format_knowledge_context(items, language_code)


def get_followup_suggestions(language_code='zh-hant', ai_mode='helper', matched_items=None, limit=3):
    """
    「你可能還想問」追問建議：取知識庫中跟目前問題同分類的其他條目標題（多語欄位）。
    問題本身在知識庫裡沒有命中任何條目時，代表沒有跟這個問題相關的資料，直接不顯示建議，
    不要用「最近更新」之類的條目硬湊，避免出現跟使用者問題無關的建議。
    """
    if ai_mode != 'helper':
        return []

    matched_items = matched_items or []
    if not matched_items:
        return []

    try:
        from .models import ChatKnowledge
        matched_ids = [item.id for item in matched_items]
        related = list(
            ChatKnowledge.objects.filter(is_active=True)
            .filter(Q(bot_type='helper') | Q(bot_type='both'))
            .exclude(id__in=matched_ids)
            .filter(category=matched_items[0].category)[:limit]
        )
    except Exception:
        return []

    suggestions = []
    for item in related:
        title = item.get_title_by_lang(language_code)
        if title and title not in suggestions:
            suggestions.append(title)
    return suggestions


# 危機關鍵字（9 語）：這是「保底安全網」——
# 只要命中，views 層會強制附上求助資源，不依賴 AI 模型自行判斷
CRISIS_KEYWORDS = [
    # 中文
    '想死', '不想活', '活不下去', '想消失', '自殺', '自杀',
    '自傷', '自伤', '傷害自己', '伤害自己', '割腕',
    '傷害別人', '伤害别人', '殺人', '杀人',
    # English
    'kill myself', 'suicide', 'self harm', 'self-harm', 'hurt myself',
    'want to die', 'end my life',
    # Tiếng Việt
    'muốn chết', 'tự tử', 'tự sát', 'không muốn sống', 'tự làm đau',
    # Bahasa Indonesia / Melayu
    'bunuh diri', 'ingin mati', 'mau mati', 'nak mati', 'tak mahu hidup',
    'tidak ingin hidup', 'menyakiti diri',
    # ภาษาไทย
    'อยากตาย', 'ฆ่าตัวตาย', 'ไม่อยากมีชีวิต', 'ทำร้ายตัวเอง',
    # 日本語
    '死にたい', '自殺', '消えたい', '自傷',
    # 한국어
    '죽고 싶', '자살', '사라지고 싶', '자해',
    # မြန်မာ
    'သေချင်', 'အသက်ရှင်ချင်မှမရှိ',
]


def contains_crisis_keywords(text):
    """判斷訊息是否含自傷 / 危機字眼（9 語保底偵測）。"""
    t = (text or '').strip().lower()
    if not t:
        return False
    return any(word in t for word in CRISIS_KEYWORDS)


def detect_friend_emotion_hint(question):
    """
    給 ReadyTo 聊天好朋友使用的初步情緒提示。
    注意：這只是提示，不是診斷，最後仍由 AI 根據上下文自然判斷。
    """
    text = (question or '').strip().lower()

    if contains_crisis_keywords(text):
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


# 問題裡常見的縣市/地區關鍵字 → 對應的中央氣象署縣市名稱，
# 也用來判斷問題是否已明確講地區（有的話天氣/地點查詢都不該再套用學校所在地）
LOCATION_KEYWORD_TO_CWA_COUNTY = {
    '台北': '臺北市', '臺北': '臺北市', '信義區': '臺北市', '大安區': '臺北市',
    '中山區': '臺北市', '松山區': '臺北市', '內湖區': '臺北市',
    '新北': '新北市', '板橋': '新北市', '新莊': '新北市', '三重': '新北市',
    '桃園': '桃園市', '桃園市': '桃園市', '中壢': '桃園市', '內壢': '桃園市', '中原': '桃園市',
    '新竹': '新竹市',
    '苗栗': '苗栗縣',
    '台中': '臺中市', '臺中': '臺中市',
    '彰化': '彰化縣',
    '南投': '南投縣',
    '雲林': '雲林縣',
    '嘉義': '嘉義市',
    '台南': '臺南市', '臺南': '臺南市',
    '高雄': '高雄市',
    '屏東': '屏東縣',
    '宜蘭': '宜蘭縣',
    '花蓮': '花蓮縣',
    '台東': '臺東縣', '臺東': '臺東縣',
    '澎湖': '澎湖縣',
    '金門': '金門縣',
    '馬祖': '連江縣',
}
LOCATION_KEYWORD_TO_CWA_COUNTY_EN = {
    'taipei': '臺北市', 'new taipei': '新北市', 'taoyuan': '桃園市',
    'hsinchu': '新竹市', 'taichung': '臺中市', 'tainan': '臺南市',
    'kaohsiung': '高雄市', 'zhongli': '桃園市', 'chungli': '桃園市',
}


def detect_explicit_county(question):
    """
    偵測問題裡是否已明確提到縣市/地區名稱，回傳中央氣象署慣用的縣市名稱（例如「臺北市」）。
    沒有提到就回傳 None，這時天氣/地點查詢才需要用學生學校所在地當預設值。
    """
    q = (question or '').strip()
    lower_q = q.lower()
    for keyword, county in LOCATION_KEYWORD_TO_CWA_COUNTY.items():
        if keyword in q:
            return county
    for keyword, county in LOCATION_KEYWORD_TO_CWA_COUNTY_EN.items():
        if keyword in lower_q:
            return county
    return None


def detect_explicit_location(question):
    """
    偵測問題裡是否已明確提到地區/城市/地點名稱。
    有的話搜尋時不需再附加學校位置。
    """
    return detect_explicit_county(question) is not None


def detect_place_query(question):
    """偵測問題是否在詢問地點或場所（餐廳、商店、辦公大樓等）。"""
    q = (question or '').strip()
    lower_q = q.lower()

    zh_keywords = [
        '餐廳', '餐館', '食堂', '小吃', '咖啡廳', '咖啡館', '咖啡',
        '便利商店', '超商', '超市', '商店', '商場', '百貨', '夜市', '市場',
        '醫院', '診所', '藥局', '銀行', '郵局', '辦公室', '辦公大樓',
        '附近', '在哪', '在哪裡', '怎麼去', '怎麼走', '地址', '哪裡有', '哪裡',
        '公園', '體育館', '游泳池', '球場', '化妝品店', '藥妝店', '屈臣氏', '康是美', '寶雅', '日藥本鋪',
        '看病', '看醫生', '掛號', '急診', '買藥', '拿藥',
        '吃飯', '吃東西', '喝飲料', '喝咖啡', '買東西', '逛街',
        '剪髮', '剪頭髮', '美髮', '健身房', '洗衣', '自助洗衣',
        '去哪', '附近有', '周邊', '學校附近', '宿舍附近',
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


def _format_place(place, language_code='zh-hant'):
    """把 Places API 單筆結果格式化成 Markdown 行。"""
    labels = _place_labels(language_code)
    sep, colon = labels['sep'], labels['colon']
    name = place.get('name', '')
    address = place.get('formatted_address', '') or place.get('vicinity', '')
    rating = place.get('rating', '')
    place_id = place.get('place_id', '')
    maps_url = f'https://www.google.com/maps/place/?q=place_id:{place_id}' if place_id else ''

    line = f'- {name}'
    if address and maps_url:
        line += f'{sep}{labels["address"]}{colon}[{address}]({maps_url})'
    elif address:
        line += f'{sep}{labels["address"]}{colon}{address}'
    if rating:
        line += f'{sep}{labels["rating"]}{colon}{rating}/5'
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
                logger.debug('Places Nearby status: %s', data.get('status'))
                if data.get('status') == 'OK':
                    results = data.get('results', [])[:3]
            except Exception as e:
                logger.warning('Places Nearby error: %s', e)

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
            logger.debug('Places Text status: %s', data.get('status'))
            if data.get('status') == 'OK':
                results = data.get('results', [])[:3]
        except Exception as e:
            logger.warning('Places Text error: %s', e)

    if not results:
        return None

    return '\n'.join(_format_place(p, language_code) for p in results)


# 學校代碼 → 中央氣象署 36 小時天氣預報用的縣市名稱。
# 依 users/school_data.py 已查核的地址推導，NKUST 官網未列地址但確定位於高雄市。
UNIVERSITY_TO_CWA_COUNTY = {
    'NTU': '臺北市', 'NCCU': '臺北市', 'NTNU': '臺北市', 'NTUST': '臺北市',
    'NTUT': '臺北市', 'NTUE': '臺北市', 'NTUB': '臺北市',
    'NTPU': '新北市', 'NOU': '新北市',
    'NCU': '桃園市',
    'NTHU': '新竹市', 'NYCU': '新竹市',
    'NCHU': '臺中市', 'NTCUST': '臺中市', 'NTCU': '臺中市', 'NTUS': '臺中市',
    'NCUE': '彰化縣',
    'NCNU': '南投縣',
    'YunTech': '雲林縣', 'NFU': '雲林縣',
    'NCYU': '嘉義市',
    'NCKU': '臺南市', 'NUTN': '臺南市',
    'NSYSU': '高雄市', 'NKUST': '高雄市', 'NKUHT': '高雄市', 'NKNU': '高雄市',
    'NPTU': '屏東縣', 'NPUST': '屏東縣',
    'NIU': '宜蘭縣',
    'NDHU': '花蓮縣',
    'NTTU': '臺東縣',
    'NUU': '苗栗縣',
    'NQU': '金門縣',
    'NPU': '澎湖縣',
}


def get_student_county(user):
    """依學生就讀學校推斷所在縣市，供天氣查詢使用；查不到時回傳 None。"""
    profile = get_student_profile(user)
    code = (getattr(profile, 'university', '') or '') if profile else ''
    return UNIVERSITY_TO_CWA_COUNTY.get(code)


def detect_weather_query(question):
    """偵測問題是否在詢問天氣、溫度、日照或颱風。"""
    q = (question or '').strip()
    lower_q = q.lower()

    zh_keywords = [
        '天氣', '氣象', '溫度', '氣溫', '幾度',
        '下雨', '會不會雨', '降雨', '雷陣雨', '會不會下雨',
        '太陽', '陽光', '會不會曬', '出太陽', '紫外線',
        '颱風', '暴風', '豪雨', '強風',
        '要不要帶傘', '要不要穿外套', '會不會冷', '會不會熱',
    ]
    en_keywords = [
        'weather', 'temperature', 'forecast', 'rain', 'rainy', 'raining',
        'sunny', 'sunshine', 'typhoon', 'storm', 'humid', 'cold', 'hot',
    ]

    return (
        any(k in q for k in zh_keywords)
        or any(k in lower_q for k in en_keywords)
    )


# ══════════════════════════════════════════
# 兩個 AI 模式的管轄範圍互相提醒
# 任務小幫手（helper）管：簽證、居留證、財力／語言證明、學校行政、入學申請等正式手續；
# 聊天好朋友（friend）管：情緒陪伴、心情、人際關係、想家、焦慮等生活與心理支持。
# 學生問到「另一個 AI 的管轄範圍」時，提醒他切換過去，而不是勉強用不擅長的模式硬答。
# ══════════════════════════════════════════
FRIEND_DOMAIN_KEYWORDS_ZH = [
    '心情不好', '心情不太好', '好難過', '想哭', '很難過', '很委屈',
    '好孤單', '很孤單', '沒有朋友', '沒朋友', '交不到朋友',
    '好想家', '很想家', '想念家人', '想家想到',
    '好焦慮', '很焦慮', '好緊張', '睡不著', '腦袋停不下來',
    '好無聊', '很無聊', '不知道要幹嘛', '不知道能幹嘛',
    '壓力好大', '壓力很大', '好累好廢', '好累', '撐不下去',
    '室友吵架', '跟室友', '跟朋友吵架', '跟男友', '跟女友', '分手了', '吵架了',
    '聽不懂老師', '中文不好很挫折', '格格不入', '不適應這裡的生活',
    '陪我聊', '陪我說說話', '想找人聊',
]
FRIEND_DOMAIN_KEYWORDS_EN = [
    'feeling down', 'feeling sad', 'i miss home', 'homesick',
    'so lonely', 'no friends', 'feeling anxious', 'stressed out',
    'i feel like crying', 'can we just talk', 'i need to vent',
]


def detect_friend_domain_query(question):
    """
    偵測問題是否屬於聊天好朋友的專長範圍（情緒陪伴、心情、人際關係）。
    只在 helper 模式「查無任何任務／資訊頁／知識庫資料」時才會被拿來判斷，
    避免把帶有情緒字眼、但其實是正式手續問題（例如財力證明的經濟壓力）誤判過去。
    """
    q = (question or '').strip()
    lower_q = q.lower()
    if not q:
        return False
    return (
        any(k in q for k in FRIEND_DOMAIN_KEYWORDS_ZH)
        or any(k in lower_q for k in FRIEND_DOMAIN_KEYWORDS_EN)
    )


# 生活機能地點推薦（餐廳、超商、健身房…），這種問題需要 Google Places 搜尋真實地點，
# 目前只有聊天好朋友有串接。刻意不放「在哪」「地址」「辦公室」這類太通用的字，
# 避免誤判成校內單位、簽證窗口這類任務小幫手自己就能正確回答的正式手續問題。
AMENITY_KEYWORDS_ZH = [
    '餐廳', '餐館', '食堂', '小吃', '咖啡廳', '咖啡館', '咖啡',
    '便利商店', '超商', '超市', '商店', '商場', '百貨', '夜市', '市場',
    '醫院', '診所', '藥局', '銀行', '郵局',
    '公園', '體育館', '游泳池', '球場', '化妝品店', '藥妝店', '屈臣氏', '康是美', '寶雅', '日藥本鋪',
    '看病', '看醫生', '掛號', '急診', '買藥', '拿藥',
    '吃飯', '吃東西', '喝飲料', '喝咖啡', '買東西', '逛街',
    '剪髮', '剪頭髮', '美髮', '健身房', '洗衣', '自助洗衣',
]
AMENITY_KEYWORDS_EN = [
    'restaurant', 'cafe', 'coffee shop', 'shop', 'store', 'mall',
    'supermarket', 'convenience store', 'hospital', 'clinic', 'pharmacy',
    'bank', 'post office', 'night market',
]


def detect_amenity_recommendation_query(question):
    """偵測問題是不是在找生活機能地點推薦（附近餐廳、超商…），不是校內單位或正式手續地點。"""
    q = (question or '').strip()
    lower_q = q.lower()
    if not q:
        return False
    return (
        any(k in q for k in AMENITY_KEYWORDS_ZH)
        or any(k in lower_q for k in AMENITY_KEYWORDS_EN)
    )


def detect_helper_domain_hit(question, user=None):
    """
    偵測問題是否命中「只有任務小幫手在管」的知識庫內容
    （bot_type 嚴格等於 helper，不含 both 共用內容）。
    用來提醒聊天好朋友：這類正式手續問題，任務小幫手有查證過的完整資料，
    自己邊聊邊answer 容易漏掉細節或講錯。
    """
    items = search_knowledge_items(question, ai_mode='helper', user=user, limit=3)
    return any(getattr(item, 'bot_type', '') == 'helper' for item in items)


def _format_cwa_forecast(data, county):
    """把中央氣象署 36 小時天氣預報 API 回應整理成人類可讀文字。"""
    try:
        locations = data['records']['location']
        location = next((l for l in locations if l.get('locationName') == county), None)
        if not location:
            return None

        elements = {el['elementName']: el['time'] for el in location['weatherElement']}
        wx_times = elements.get('Wx', [])
        pop_times = elements.get('PoP', [])
        min_t_times = elements.get('MinT', [])
        max_t_times = elements.get('MaxT', [])

        if not wx_times:
            return None

        lines = [f'{county}天氣預報（中央氣象署）：']
        for i in range(min(len(wx_times), 3)):
            start = wx_times[i]['startTime']
            wx = wx_times[i]['parameter']['parameterName']
            pop = pop_times[i]['parameter']['parameterName'] if i < len(pop_times) else ''
            min_t = min_t_times[i]['parameter']['parameterName'] if i < len(min_t_times) else ''
            max_t = max_t_times[i]['parameter']['parameterName'] if i < len(max_t_times) else ''

            time_label = start[5:16].replace('-', '/').replace('T', ' ')
            line = f'- {time_label} 起：{wx}'
            if min_t and max_t:
                line += f'，氣溫 {min_t}~{max_t}°C'
            if pop:
                line += f'，降雨機率 {pop}%'
            lines.append(line)

        return '\n'.join(lines)
    except Exception:
        return None


class _GovCertCompatAdapter(HTTPAdapter):
    """
    部分政府機關網站（例如中央氣象署開放資料平臺）的憑證缺少
    Subject Key Identifier 擴充欄位，Python 3.13 預設會用嚴格模式
    （VERIFY_X509_STRICT）擋下連線，但瀏覽器與 curl 都能正常連線，
    代表憑證鏈本身仍是可信的，只是不符合這一項嚴格規範。

    這裡只關閉 VERIFY_X509_STRICT 這一項檢查，其餘憑證鏈驗證、
    主機名稱比對都維持正常，跟直接關閉憑證驗證（verify=False）不同，
    不應被當成一般的「忽略憑證錯誤」處理方式來重用。
    """

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        if hasattr(ssl, 'VERIFY_X509_STRICT'):
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def _cwa_get(url, params, timeout=5):
    """對中央氣象署開放資料平臺發送請求，處理其憑證的相容性問題。"""
    session = http_requests.Session()
    session.mount('https://', _GovCertCompatAdapter())
    return session.get(url, params=params, timeout=timeout)


def fetch_weather_forecast(county):
    """
    查詢中央氣象署 36 小時天氣預報。
    沒有設定 API key、查無資料、或連線失敗時一律回傳 None，
    由呼叫端決定如何告知學生，不在這裡編造天氣資料。
    """
    api_key = getattr(settings, 'CWA_API_KEY', '')
    if not api_key or not county:
        return None

    try:
        resp = _cwa_get(
            'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001',
            params={'Authorization': api_key, 'locationName': county},
        )
        data = resp.json()
        if str(data.get('success')).lower() != 'true':
            logger.warning('CWA forecast API returned failure for %s', county)
            return None
        return _format_cwa_forecast(data, county)
    except Exception as e:
        logger.warning('CWA forecast error: %s', e)
        return None


def fetch_typhoon_bulletin():
    """
    查詢中央氣象署現有颱風警報。沒有作用中的颱風、沒有設定 API key、
    或連線失敗時回傳 None（None 不代表「沒有颱風」，呼叫端仍應以此為「查無資料」處理，
    不可用來斷定安全無虞）。
    """
    api_key = getattr(settings, 'CWA_API_KEY', '')
    if not api_key:
        return None

    try:
        resp = _cwa_get(
            'https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0034-005',
            params={'Authorization': api_key},
        )
        data = resp.json()
        typhoons = data.get('records', {}).get('tropicalCyclones', {}).get('tropicalCyclone', [])
        if not typhoons:
            return None

        lines = ['目前中央氣象署發布的颱風警報：']
        for typhoon in typhoons[:2]:
            name = typhoon.get('typhoonName', '') or typhoon.get('cwaTyphoonName', '')
            lines.append(f'- 颱風「{name}」，詳細警戒範圍與強度請查中央氣象署官網確認最新消息。')
        return '\n'.join(lines)
    except Exception as e:
        logger.warning('CWA typhoon error: %s', e)
        return None


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
        r'\n*👉?\s*前往資訊頁面：\s*\[[^\]]+\]\([^)]+\)\s*',
        r'\n*👉?\s*前往資訊頁面：\s*【[^】]+】\([^)]+\)\s*',
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



def build_attachment_input_content(attachments):
    """
    將使用者上傳的附件轉成 OpenAI Responses API 可用的 content blocks。

    - 圖片／拍照：以 base64 data URL 提供給模型的視覺輸入。
    - PDF：以 base64 file_data 提供給模型的檔案輸入。
    - 可解碼成文字的檔案（txt/csv/md/json 等）：直接把文字內容放進 prompt。
    - 其他無法讀取內容的檔案：只在摘要中列出檔名，提示模型無法讀取內容。
    """
    content_blocks = []
    summary_lines = []

    for attachment in attachments:
        name = attachment.original_name or attachment.file.name

        attachment.file.open('rb')
        try:
            data = attachment.file.read()
        finally:
            attachment.file.close()

        mime_type, _ = mimetypes.guess_type(name)
        mime_type = mime_type or 'application/octet-stream'

        if attachment.attachment_type in ('image', 'camera') or mime_type.startswith('image/'):
            b64 = base64.b64encode(data).decode('utf-8')
            content_blocks.append({
                'type': 'input_image',
                'image_url': f'data:{mime_type};base64,{b64}',
            })
            summary_lines.append(f'【圖片附件】{name}')
        elif mime_type == 'application/pdf':
            b64 = base64.b64encode(data).decode('utf-8')
            content_blocks.append({
                'type': 'input_file',
                'filename': name,
                'file_data': f'data:{mime_type};base64,{b64}',
            })
            summary_lines.append(f'【PDF 附件】{name}')
        else:
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                text = None

            if text is not None:
                if len(text) > 8000:
                    text = text[:8000] + '\n...(內容過長，已截斷)'
                content_blocks.append({
                    'type': 'input_text',
                    'text': f'【檔案附件：{name}】\n{text}',
                })
                summary_lines.append(f'【檔案附件】{name}')
            else:
                summary_lines.append(f'【檔案附件，目前無法讀取此格式內容】{name}')

    return content_blocks, '\n'.join(summary_lines)


def generate_ai_reply(*, user, question, recent_messages, ai_mode="helper", attachments=None, role="", personality=""):
    """產生 AI 回覆。helper 使用兩段格式；friend 使用自然聊天格式。"""

    attachments = attachments or []

    if ai_mode not in ["helper", "friend"]:
        ai_mode = "helper"

    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    logger.debug('openai api_key configured: %s', bool(api_key))

    language_code, language_source = choose_reply_language(question)
    personal_label, general_label = ANSWER_LABELS.get(
        language_code,
        ANSWER_LABELS['zh-hant']
    )
    language_en = LANGUAGE_LABELS_EN.get(language_code, 'Traditional Chinese')
    friend_emotion_hint = detect_friend_emotion_hint(question)

    profile_context = build_user_profile_context(user)
    crisis_resources = build_crisis_resources(user)
    # helper 模式沒有像 friend 模式在 views.py 那樣的關鍵字保底安全網，
    # 危機指令完全交給 LLM 自行判斷語氣很容易誤觸發（例如學生只是語氣不耐煩、反駁），
    # 所以先用關鍵字判斷：沒有命中明確危機字眼時，直接不把危機指令放進 prompt，
    # 避免模型被鄰近的強指令帶著聯想成危機
    is_crisis_message = contains_crisis_keywords(question)
    if is_crisis_message:
        crisis_block = f"""
【危機求助資源】這則訊息含有明確的自傷、想死、傷害他人等危機字眼，請優先處理安全：
- 提醒學生不要獨處，立刻聯絡可信任的人、學校輔導中心或家人朋友。
- 如果已經受傷或有立即危險，先提醒撥打 119 緊急醫療救護專線。
- 將以下求助資源原文複製到回覆中，電話連結格式必須完整保留：
{crisis_resources}
- 不要承諾保密，不要說 AI 可以單獨處理危機。
""".strip()
    else:
        crisis_block = (
            '【危機求助資源】這則訊息沒有偵測到明確的自傷、想死、傷害他人等危機字眼，'
            '請正常回答學生實際問的問題就好，不要主動提起自殺防治專線等求助資源；'
            '單純的情緒化、不耐煩、反駁、開玩笑不算危機，不要誤判。'
        )
    flow_context = build_student_flow_context(user, language_code)
    # 學生就讀學校的校務資料（地址、總機、國際處、校內單位位置與分機），
    # 讓「校長室在哪裡」這類問題可以直接依個人資料定位回答
    school_context = build_school_context(user, language_code)

    # RAG 檢索（依關聯度排序），items 同時供「你可能還想問」追問建議使用
    knowledge_items = search_knowledge_items(question, ai_mode=ai_mode, user=user)
    knowledge_context = format_knowledge_context(knowledge_items, language_code)
    suggestions = get_followup_suggestions(
        language_code, ai_mode=ai_mode, matched_items=knowledge_items
    )

    if not knowledge_context.strip():
        knowledge_context = '目前沒有找到直接相關的知識庫資料。'

    if ai_mode == 'friend':
        history_text = build_history_text(recent_messages, max_user_messages=6)
    else:
        history_text = build_history_text(recent_messages)

    # 小老師角色：課業輔助載入學群課業背景包；生活指導載入生活知識背景包
    is_tutor_role = ai_mode == 'helper' and (role or '').strip() == '小老師'
    is_life_guidance = is_tutor_role and (personality or '').strip() == '生活指導'
    if is_life_guidance:
        tutor_context = build_life_guidance_context(user, language_code)
    elif is_tutor_role:
        tutor_context = build_tutor_context(user, language_code)
    else:
        tutor_context = ''

    if not tutor_context:
        tutor_block = ''
    elif is_life_guidance:
        tutor_block = (
            '【小老師生活背景包】以下是依這位學生的學校、國籍與身分別載入的生活知識。'
            '回答生活問題時請結合這些內容，並針對他的身分別與國籍給具體做法；'
            '背景包沒有涵蓋的細節，請誠實說明並建議他詢問學校國際處或宿舍管理員，不要自行編造規定與費用。\n'
            + tutor_context
        )
    else:
        tutor_block = (
            '【小老師課業背景包】以下是這位學生的系所、學群與對應的課業知識。'
            '回答課業問題時請結合這些內容：用他系所的課程舉例、推薦背景包中的免費學習資源；'
            '背景包沒有涵蓋的細節（如特定學校的課表），請誠實說明並建議他查詢系辦或課程大綱。\n'
            + tutor_context
        )

    info_page = get_personalized_info_page(user, question)
    task_link = get_relevant_student_task(user, question, language_code) if ai_mode == "helper" else None

    # 依個人資料定位的規則：學生問「校長室在哪」「國際處分機幾號」時，
    # 先用他自己學校的資料回答，不要反問「你是哪間學校」，也不要編造沒有的分機
    if school_context:
        school_block = f"""
【學生就讀學校的校務資料】以下是這位學生個人資料所填學校的實際資料：
{school_context}

依個人資料定位的規則：
1. 學生問校內地點、單位、分機、行事曆、校務流程時，預設就是在問「他自己的學校」，直接用上面的資料回答，不要反問他是哪一間學校。
2. 上面資料沒有涵蓋的單位或分機，直接說明你沒有這項資料，並請他打學校總機或查官網，絕對不可以自行編造地點、分機或電話號碼。
3. 學生明確問其他學校時，才改用一般說明，並提醒他這不是他就讀的學校。

【不可以自己講日期】
你手上沒有任何一年的正確日期資料，所以任何具體日期都不可以憑印象說出來
（例如「9 月 9 日開學」「3 月 15 日截止」），即使你覺得自己知道，也不可以。
講錯開學日或報到期限，學生可能訂錯機票、錯過註冊，後果比回答不出來嚴重得多。

【什麼時候可以給「學校行事曆」連結】
只有在學生問的是「他自己學校的學期行程」時才給，也就是這幾類：
開學日、放假與寒暑假起訖、註冊繳費期限、選課與加退選時間、期中期末考週、畢業相關流程時程。
這些才是學校行事曆上真的會寫的東西。

【什麼時候「不可以」給學校行事曆連結】
以下這些的日期不會出現在學校行事曆上，把行事曆丟給學生是答非所問，不要這樣做：
- 校外或全國性的競賽、比賽、檢定考試（例如大專資訊應用競賽、TOCFL、多益）
- 其他單位主辦的活動、營隊、講座、說明會
- 獎學金、計畫、實習的報名或截止日
- 政府機關的辦理時程（簽證、居留證、健保）
- 系所或社團自己辦的活動
遇到這幾類，請誠實說明你沒有可靠的最新資訊，並建議他直接查「主辦單位」的官方網站或公告，
必要時可以請他洽詢系辦、學務處課外活動組或該競賽的官方網站。不要用學校行事曆搪塞。

【線上系統】
選課、成績、請假這類要登入操作的問題，把上面「線上系統」對應的連結給他。
""".strip()
    else:
        school_block = (
            '【學生就讀學校的校務資料】系統目前沒有這位學生學校的校務資料。'
            '遇到校內地點、單位、分機問題時，請說明你沒有該校資料，'
            '建議他查學校官網或撥打總機，不要編造地點與號碼。'
        )

    # 任務清單和資訊中心都沒有相關資料時，helper 模式直接回答，不分個人化/一般回答兩段；
    # 小老師角色一律用自然教學語氣回答，不套用個人化/一般回答兩段格式
    direct_mode = ai_mode == "helper" and not is_tutor_role and not task_link and not info_page

    # 管轄範圍互相提醒（helper → friend）：
    # 任務、資訊頁、知識庫都查無資料時，才判斷這是不是其實是聊天好朋友的專長
    # （情緒陪伴、天氣查詢、生活機能地點推薦——天氣和地點都只有 friend 模式串接了真實 API，
    # helper 自己回答只會編造或含糊帶過），避免把帶情緒字眼的正式手續問題誤判過去；
    # 危機訊息已由上面的 crisis_block 處理，優先權更高，這裡不重複判斷。
    friend_domain_hint = ''
    if direct_mode and not is_crisis_message:
        if detect_friend_domain_query(question):
            friend_domain_hint = (
                '【任務歸屬提醒】這個問題聽起來比較像是情緒或生活陪伴需求'
                '（例如心情不好、想家、人際關係、壓力大），這其實是「ReadyTo 聊天好朋友」的專長，'
                '不是任務小幫手負責的簽證、居留證等正式手續。'
                '請先用 1、2 句話簡短、溫暖地回應學生的感受，不要勉強套用個人化/一般回答的格式，'
                '再自然地建議他切換到「ReadyTo 聊天好朋友」，那邊比較適合陪他聊這件事。'
            )
        elif detect_weather_query(question):
            friend_domain_hint = (
                '【任務歸屬提醒】這是天氣查詢，任務小幫手沒有串接氣象資料，這其實是「ReadyTo 聊天好朋友」的專長'
                '（那邊串接了中央氣象署的即時資料）。'
                '請用 1、2 句話簡短回應，絕對不要自己編造溫度、降雨機率、颱風等任何天氣數字，'
                '直接建議他切換到「ReadyTo 聊天好朋友」查詢天氣。'
            )
        elif detect_amenity_recommendation_query(question):
            friend_domain_hint = (
                '【任務歸屬提醒】這是生活機能地點推薦（例如附近餐廳、超商、健身房），'
                '任務小幫手沒有串接地圖服務，這其實是「ReadyTo 聊天好朋友」的專長（那邊串接了 Google 地圖搜尋真實地點）。'
                '請用 1、2 句話簡短回應，絕對不要自己編造或推薦任何地點名稱與地址，'
                '直接建議他切換到「ReadyTo 聊天好朋友」查詢附近地點。'
            )

    place_results = None
    place_source = None
    if ai_mode == 'friend' and detect_place_query(question):
        # 校內單位（校長室、國際處…）不是 Google 地圖上找得到的地標，
        # 先比對學生學校自己的 SchoolUnit 資料，比 Google 關鍵字亂猜準確
        school = get_student_school(user)
        matched_units = search_school_units(school, question)
        if matched_units:
            place_results = '\n'.join(_format_school_unit(unit, school, language_code) for unit in matched_units[:3])
            place_source = 'school_unit'
        else:
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

            if place_results:
                place_source = 'google'
            elif knowledge_items:
                # Google 地圖也查無此地點，退回知識庫找相關資料
                place_results = knowledge_context
                place_source = 'knowledge'

    place_hint = ''
    if place_source in ('google', 'school_unit'):
        place_hint = '【地點查詢】學生詢問附近地點，系統已根據學生所在學校搜尋到真實地點，地點列表會自動附在你的回覆後面。你只需要用 1 句話自然回應（例如「幫你找到幾個不錯的選擇！」），不要自己列出地名或地址，也不要編造或推薦任何沒在列表裡的地方。'
    elif place_source == 'knowledge':
        place_hint = '【地點查詢】學生詢問的地點在地圖上查不到，但知識庫剛好有相關資料，資料會自動附在你的回覆後面。你只需要用 1 句話自然帶到（例如「幫你查到相關資訊囉！」），不要自己編造地點或地址，也不要重複列出知識庫的內容。'

    logger.debug('ai_mode=%s, place_results=%s, place_source=%s', ai_mode, bool(place_results), place_source)

    # 天氣查詢：與地點查詢同一套設計，AI 只負責一句話帶到，實際數字一律來自中央氣象署，不可自行編造
    weather_results = None
    weather_hint = ''
    if ai_mode == 'friend' and detect_weather_query(question):
        # 問題裡有明確講縣市（例如「臺北天氣怎麼樣」）就查那個縣市，
        # 沒有明確講地區（例如「今天天氣如何」）才退回學生學校所在地
        county = detect_explicit_county(question) or get_student_county(user)
        weather_results = fetch_weather_forecast(county) if county else None

        if '颱風' in question or 'typhoon' in question.lower():
            typhoon_bulletin = fetch_typhoon_bulletin()
            if typhoon_bulletin:
                weather_results = (
                    f'{weather_results}\n\n{typhoon_bulletin}' if weather_results else typhoon_bulletin
                )

        if weather_results:
            weather_hint = '【天氣查詢】學生詢問天氣相關問題，系統已查詢中央氣象署的真實資料，資料會自動附在你的回覆後面。你只需要用 1 句話自然回應（例如「幫你查到天氣資訊囉！」），不要自己說出溫度、降雨機率等具體數字，也不要編造任何天氣狀況。'
        elif county:
            weather_hint = '【天氣查詢】學生詢問天氣，但目前查詢不到氣象資料（可能是氣象署服務暫時無法連線）。請誠實告知你現在查不到即時天氣，建議他查中央氣象署官網或天氣 App，絕對不可以自己編造溫度、降雨機率或颱風狀況。'
        else:
            weather_hint = '【天氣查詢】學生詢問天氣，但系統不知道他就讀哪所學校、無法判斷地區。請直接問他想查哪個城市的天氣，不要編造天氣資料。'

    logger.debug('ai_mode=%s, weather_results=%s', ai_mode, bool(weather_results))

    # 管轄範圍互相提醒（friend → helper）：
    # 學生在聊天好朋友問到簽證、居留證、學校行政等正式手續，
    # 提醒他去問任務小幫手，那邊有查證過的完整資料，不要讓 friend 憑印象隨口回答。
    cross_domain_hint = ''
    if ai_mode == 'friend' and detect_helper_domain_hit(question, user):
        cross_domain_hint = (
            '【任務歸屬提醒】這個問題其實屬於「ReadyTo 任務小幫手」的專業範圍'
            '（例如簽證、居留證、財力／語言證明、學校行政等正式手續），'
            '任務小幫手那邊有經過查證的完整資料。'
            '你可以先用 1、2 句話簡短回應，但不要給出詳細步驟或保證細節正確，'
            '並自然地建議學生切換到「ReadyTo 任務小幫手」問這類問題。'
        )

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

    # helper 模式：如果知識庫命中的文章「全部屬於同一分類」，就用穩定的本地知識庫答案，避免多花 API
    # （例如簽證命中「通則」+「該國別」兩篇都算 visa 分類，原文拼接仍然是同一個主題，沒問題）。
    # 命中好幾篇「不同分類」時，代表題目籠統或搜尋詞誤中好幾個不同主題，
    # 直接原文拼接會把不相關的內容也一起丟給學生（問護照卻連簽證、僑生海聯招都貼出來），
    # 這種情況要走 OpenAI，讓它自己判斷只回答學生實際問的部分。
    #
    # school_info 這個分類本身是「整校校內單位總覽」的長文，就算只命中這一篇也不能直接整篇貼出去——
    # 學生問「地址」「校長室在哪」只是想知道其中一行，原文照貼會把全部單位都列出來，
    # 一樣要走 OpenAI 讓它從文章裡挑出真正被問到的那一項。
    #
    # 但如果學生有上傳附件，必須走 OpenAI 才能讀取附件內容，不能用這個本地捷徑；
    # 小老師角色一律走 OpenAI，才能維持教學語氣與課業背景包，不要用這個直接回答的捷徑。
    # friend_domain_hint 有值代表這題其實該轉給聊天好朋友（天氣、地點推薦、情緒陪伴），
    # 就算知識庫剛好也搜到東西，也要走 OpenAI 講出轉介提醒，不要用本地捷徑蓋掉這個提醒。
    DIRECTORY_STYLE_CATEGORIES = {'school_info'}
    knowledge_categories = {item.category for item in knowledge_items}
    if ai_mode == "helper" and not attachments and not is_tutor_role and not friend_domain_hint and len(knowledge_categories) == 1 and not (knowledge_categories & DIRECTORY_STYLE_CATEGORIES) and (
        knowledge_context
        and '目前沒有找到直接相關的知識庫資料' not in knowledge_context
        and '目前沒有可用的知識庫資料' not in knowledge_context
        and '目前知識庫欄位與資料庫尚未同步' not in knowledge_context
    ):
        if direct_mode:
            # 任務清單和資訊中心都沒有相關資料，不分段，直接用知識庫內容回答
            return {
                'reply': knowledge_context,
                'source': 'knowledge_base_direct',
                'model': 'local-knowledge',
                'suggestions': suggestions,
            }

        # 本地個人化引擎：以學生「真實」任務狀態 + 截止日組出個人化段落（零幻覺）；
        # 沒有個人資料時才退回多語罐頭句
        personal_text = (
            build_local_personal_answer(user, question, language_code)
            or KNOWLEDGE_DIRECT_PERSONAL.get(language_code, KNOWLEDGE_DIRECT_PERSONAL['zh-hant'])
        )
        reply = (
            f'{personal_label}：\n'
            f'{personal_text}\n\n'
            f'{general_label}：\n'
            f'{knowledge_context}'
        )
        # 附上相關任務連結，讓學生可以一鍵跳到任務清單
        reply = insert_info_links_after_personalized_answer(
            reply=reply,
            info_page=info_page,
            personal_label=personal_label,
            general_label=general_label,
            task_link=task_link,
            language_code=language_code,
        )
        return {
            'reply': reply,
            'source': 'knowledge_base_direct',
            'model': 'local-knowledge',
            'suggestions': suggestions,
        }

    content_blocks, attachment_summary = build_attachment_input_content(attachments)
    attachment_note = (
        f'\n\n學生上傳了以下附件，請根據附件實際內容回答，不要假設或編造看不到的內容：\n{attachment_summary}'
        if attachment_summary else ''
    )

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

{place_hint}

{weather_hint}

{cross_domain_hint}

以下是最近對話紀錄（請根據這些內容自然銜接，不要當作第一次對話）：
{history_text}

學生最新想聊的內容：
{question}{attachment_note}

請用 ReadyTo 聊天好朋友的身份回答。

你的核心角色：
你不是行政流程機器人，而是像一位真誠、會聽人說話、有情緒反應的朋友。
你要根據學生當下的語氣、情緒與問題內容，切換不同的陪伴方式。
你的回答要自然、有溫度、像真人朋友，不要像客服、公告、報告或心理學教科書。

重要原則：
1. 不要使用「{personal_label}」或「{general_label}」標題。
2. 不要使用「個人化回答 / 一般回答」兩段格式。
3. 不要輸出「情緒分類：...」。
4. 不要一開始就講道理，直接自然回應學生當下那句話。
5. 不要假裝自己是心理師、醫生、學校官方單位或緊急救援人員。
6. 不要做醫療診斷，不要說學生有憂鬱症、焦慮症等診斷。
7. 不要每次都條列式回答，除非學生明確要求整理。
8. 不要用换句話說的方式重複肯定學生剛剛講的話或情緒，再接下一句。例如學生說「最近壓力很大」，不要回「壓力大真的很讓人疲憊，最近發生了什麼讓你特別感到有壓力的事嗎？」，直接回「最近發生了什麼讓你特別感到有壓力的事嗎？」就好。理解要放進你怎麼回應裡，不用先講一句總結他感受的話當開場。

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
6. 反問前不要先加一句換句話說學生感受的開場白，問題本身就是回應，直接問就好。

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
每次回答最多寫 2 句，以下情況例外：
- 自傷或危機狀況：完整給出求助方式，不限長度。
- 提供地點搜尋結果：直接列出地點名稱和地址連結，列幾個就寫幾個。
一個句子只說一件事，不要塞多個意思進去。

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
    elif is_tutor_role:
        input_text = f"""
[LANGUAGE REQUIREMENT] Your entire reply MUST be in {language_en} only. Do not use any other language.

不要使用「{personal_label} / {general_label}」兩段格式，也不要輸出這兩個標題，直接用有教學感的自然語氣回答。

以下是學生基本資料，僅供你理解背景，不要生硬列出：
{profile_context}

{school_block}

{tutor_block}

以下是系統 FAQ / 知識庫搜尋結果，如果和學生的課業問題相關可以參考，不相關就不要勉強使用：
{knowledge_context}

以下是最近對話紀錄（請根據這些內容自然銜接，不要當作第一次對話）：
{history_text}

學生最新的課業問題：
{question}{attachment_note}

{crisis_block}

[REMINDER] Write your answer in {language_en} only. Answer directly in a warm, teaching tone. Do not split it into labeled sections.
""".strip()
    elif direct_mode:
        input_text = f"""
[LANGUAGE REQUIREMENT] Your entire reply MUST be in {language_en} only. Do not use any other language.

這個問題在網站的任務清單和資訊中心都沒有找到相關資料，不要使用「{personal_label} / {general_label}」兩段格式，也不要輸出這兩個標題。

以下是學生基本資料：
{profile_context}

{school_block}

{friend_domain_hint}

以下是系統 FAQ / 知識庫搜尋結果，僅供參考，裡面可能包含好幾個不同主題（因為搜尋是關鍵字比對，不代表每篇都跟學生的問題相關）：
{knowledge_context}

只回答學生這次實際問的問題。上面的知識庫資料如果有哪一段直接對應這個問題，就根據那一段回答；
其他不相關的段落（不同主題、不同證件、不同流程、或同一篇列表裡跟問題無關的其他項目）一律忽略，
絕對不要因為它剛好在同一篇知識庫資料裡就整篇貼出來——例如學生只問地址，就只回地址，不要把其他單位、電話、分機全部列出來。
如果整份知識庫資料都沒有直接回答到問題，且上面沒有提醒學生改問聊天好朋友，就憑你自己對來臺就學流程的知識直接回答，絕對不可以把「目前沒有找到直接相關的知識庫資料」或任何系統提示語直接輸出為答案。

以下是最近對話紀錄，僅供上下文參考：
{history_text}

學生最新問題：
{question}{attachment_note}

{crisis_block}

[REMINDER] Write your answer in {language_en} only. Answer the question directly in one concise passage. Do not split it into labeled sections.
""".strip()
    else:
        input_text = f"""
[LANGUAGE REQUIREMENT] Your entire reply MUST be in {language_en} only. Do not use any other language.

以下是學生自己的基本資料，僅供「{personal_label}」參考：
{profile_context}

{school_block}
（校務資料屬於個人化資訊，請用在「{personal_label}」，不要寫進「{general_label}」。）

以下是學生目前的流程任務與提醒資料，僅供「{personal_label}」使用：
{flow_context}

以下是系統提供的資訊區頁面與附件資料，僅供「{personal_label}」參考：
{info_page or '目前沒有對應的資訊區頁面。'}

以下是系統 FAQ / 知識庫搜尋結果，必須優先用於「{general_label}」：
{knowledge_context}

如果知識庫有直接相關內容，「{general_label}」必須根據知識庫回答，不要忽略。
如果知識庫沒有找到相關資料，「{general_label}」必須根據你自己對來臺就學流程的知識直接回答學生的問題，不要參考學生的身份、國籍、學校等個人資料，絕對不可以把「目前沒有找到直接相關的知識庫資料」或任何系統提示語直接輸出為答案。

以下是最近對話紀錄，僅供上下文參考：
{history_text}

學生最新問題：
{question}{attachment_note}

{crisis_block}

[REMINDER] Write your answer in {language_en} only. Use this exact format:
{personal_label}：
根據學生的任務狀況與個人資料，說明他目前與這個問題相關的任務進度、還需要完成哪些步驟，以及這些任務和問題之間的關聯。
不要逐步教學或列出操作指南，只需描述他目前的狀況與脈絡。

{general_label}：
...
""".strip()

    try:
        client = OpenAI(api_key=api_key)

        if content_blocks:
            api_input = [{
                'role': 'user',
                'content': [{'type': 'input_text', 'text': input_text}] + content_blocks,
            }]
        else:
            api_input = input_text

        response = client.responses.create(
            model=model,
            instructions=build_system_instructions(language_code, language_source, ai_mode, role=role, personality=personality, direct_mode=direct_mode),
            input=api_input,
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
            'place_results_text': place_results,
            'weather_results_text': weather_results,
            'source': 'openai',
            'model': model,
            'suggestions': suggestions,
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

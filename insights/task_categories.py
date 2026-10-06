"""
insights/task_categories.py
把 flows.Task 對應到分析分類。

task_code 是自由輸入的字串，因此：
1. 先查 TASK_CODE_MAP（明確對照，優先）
2. 查不到時，用 task_code + 中英文標題做關鍵字比對
3. 都沒對到 → 'other'

執行 `python manage.py build_insights` 時會列出被歸到 other 的任務，
請把它們的 task_code 補進 TASK_CODE_MAP。
"""

from chatbot.services import keyword_matches

# 分析分類（順序即畫面顯示順序）
TASK_CATEGORY_CHOICES = [
    ('entry_permit', '簽證／入出境許可'),
    ('residence_permit', '居留證件'),
    ('nhi', '全民健保'),
    ('housing', '住宿'),
    ('registration', '報到註冊'),
    ('health_check', '健康檢查'),
    ('course', '選課'),
    ('other', '其他'),
]
TASK_CATEGORY_LABELS = dict(TASK_CATEGORY_CHOICES)

# ── 明確對照：task_code（小寫）→ 分析分類 ──
# 簽證、居留證、健保等任務已由下方關鍵字規則正確分類，這裡只補關鍵字抓不到的。
# 刻意留在 other 的：護照、良民證、財力證明、學歷驗證、翻譯、照片等「申請文件準備」，
# 以及機票、換錢、手機門號、銀行開戶、社團等生活事項——它們不是校方要追蹤的行政流程本身，
# 併入會稀釋流程完成率的意義。
TASK_CODE_MAP = {
    'apply_visa': 'entry_permit',
    'apply_entry_permit': 'entry_permit',
    'apply_arc': 'residence_permit',
    'apply_nhi': 'nhi',
    # 報到註冊
    'pay_tuition_and_fees': 'registration',
    'activate_school_portal_account': 'registration',
    # 選課（抵免、分級測驗決定修哪些課）
    'freshman_english_credit_exemption': 'course',
    'attend_chinese_placement_test': 'course',
    'delayed_chinese_placement': 'course',
}

# ── 關鍵字比對（依序比對，先命中先贏）──
# 順序有意義：
# - 「居留簽證」含「居留」，但它是簽證 → entry_permit 的「簽證」要排在 residence_permit 前面
# - 「臺灣地區居留入出境證」（港澳生）含「入出境」，但它是居留證件 → residence_permit 排在「入出境許可」前面
# - 「Course enrollment」要歸選課 → course 排在 registration 前面
KEYWORD_RULES = [
    ('entry_permit', ['visa', '簽證']),
    ('residence_permit', ['arc', 'residence permit', 'resident certificate', '居留']),
    ('entry_permit', ['entry permit', '入出境許可', '入境許可']),
    ('health_check', ['health check', 'health exam', 'medical exam', 'physical exam', '健康檢查', '健檢', '體檢']),
    ('nhi', ['nhi', 'national health insurance', '健保', '全民健康保險']),
    ('housing', ['housing', 'dorm', 'dormitory', '宿舍', '住宿', '租屋']),
    ('course', ['course', '選課', '加退選']),
    ('registration', ['registration', 'register', 'check-in', 'enrollment', '報到', '註冊']),
]


def classify_task(task):
    """回傳 Task 的分析分類代碼。"""
    code = (task.task_code or '').strip().lower()
    if code in TASK_CODE_MAP:
        return TASK_CODE_MAP[code]

    text = f'{code.replace("_", " ")} {(task.title or "").lower()} {(task.title_en or "").lower()}'
    for category, keywords in KEYWORD_RULES:
        if any(keyword_matches(k, text) for k in keywords):
            return category
    return 'other'

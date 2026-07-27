"""
提醒訊息的多語言範本（純函式，不依賴 models，避免與 flows.models 互相 import 造成循環引用）。

被三個地方使用：
- flows.reminders.sync_task_reminders：到期提醒（產生 Reminder.message + 寄送 Email）
- flows.models 的 post_save signal：跳過前置任務提醒
- flows.models.Reminder.get_message：小鈴鐺依目前瀏覽頁面的語言即時翻譯提醒內容
"""

# 與 Task.get_title_by_lang / get_localized 相同的慣例：'' 代表繁體中文（預設）
SUPPORTED_LANGS = {'en', 'my', 'id', 'ms', 'th', 'ja', 'ko', 'vi'}


def normalize_lang(lang_code):
    """把語言代碼（如 'zh-hant'、'en-us'）轉成本模組使用的短代碼；不支援的語言一律回退中文（''）。"""
    lang_code = (lang_code or '').lower()
    short = lang_code.split('-')[0] if '-' in lang_code else lang_code
    return short if short in SUPPORTED_LANGS else ''


def render_due_message(kind, lang, task_title, due_date, days_left=None):
    """kind: 'overdue' | 'due_today' | 'due_soon'"""
    templates = {
        '': {
            'overdue': f'您的任務「{task_title}」已過期（期限：{due_date}），請盡速完成。',
            'due_today': f'您的任務「{task_title}」今天到期，請記得完成。',
            'due_soon': f'您的任務「{task_title}」將於 {days_left} 天後到期（{due_date}）。',
        },
        'en': {
            'overdue': f'Your task "{task_title}" is overdue (Deadline: {due_date}). Please complete it as soon as possible.',
            'due_today': f'Your task "{task_title}" is due today. Please remember to complete it.',
            'due_soon': f'Your task "{task_title}" will expire in {days_left} day(s) (Deadline: {due_date}).',
        },
        'vi': {
            'overdue': f'Nhiệm vụ "{task_title}" của bạn đã quá hạn (Hạn chót: {due_date}). Vui lòng hoàn thành càng sớm càng tốt.',
            'due_today': f'Nhiệm vụ "{task_title}" của bạn đến hạn hôm nay. Hãy nhớ hoàn thành nhé.',
            'due_soon': f'Nhiệm vụ "{task_title}" của bạn sẽ hết hạn sau {days_left} ngày nữa (Hạn chót: {due_date}).',
        },
        'id': {
            'overdue': f'Tugas Anda "{task_title}" telah lewat batas waktu (Tenggat: {due_date}). Harap segera diselesaikan.',
            'due_today': f'Tugas Anda "{task_title}" jatuh tempo hari ini. Jangan lupa untuk menyelesaikannya.',
            'due_soon': f'Tugas Anda "{task_title}" akan berakhir dalam {days_left} hari (Tenggat: {due_date}).',
        },
        'ms': {
            'overdue': f'Tugasan anda "{task_title}" telah tamat tempoh (Tarikh akhir: {due_date}). Sila selesaikan secepat mungkin.',
            'due_today': f'Tugasan anda "{task_title}" perlu diselesaikan hari ini. Jangan lupa untuk menyelesaikannya.',
            'due_soon': f'Tugasan anda "{task_title}" akan tamat tempoh dalam {days_left} hari (Tarikh akhir: {due_date}).',
        },
        'th': {
            'overdue': f'งาน "{task_title}" ของคุณเลยกำหนดแล้ว (กำหนดส่ง: {due_date}) กรุณาดำเนินการให้เสร็จโดยเร็วที่สุด',
            'due_today': f'งาน "{task_title}" ของคุณครบกำหนดวันนี้ กรุณาอย่าลืมทำให้เสร็จ',
            'due_soon': f'งาน "{task_title}" ของคุณจะครบกำหนดในอีก {days_left} วัน (กำหนดส่ง: {due_date})',
        },
        'ja': {
            'overdue': f'あなたのタスク「{task_title}」は期限切れです（期限：{due_date}）。至急完了してください。',
            'due_today': f'あなたのタスク「{task_title}」は本日が期限です。忘れずに完了してください。',
            'due_soon': f'あなたのタスク「{task_title}」はあと{days_left}日で期限を迎えます（期限：{due_date}）。',
        },
        'ko': {
            'overdue': f'"{task_title}" 작업이 기한을 넘겼습니다 (기한: {due_date}). 가능한 빨리 완료해 주세요.',
            'due_today': f'"{task_title}" 작업이 오늘 마감입니다. 잊지 말고 완료해 주세요.',
            'due_soon': f'"{task_title}" 작업이 {days_left}일 후 마감됩니다 (기한: {due_date}).',
        },
        'my': {
            'overdue': f'သင်၏လုပ်ငန်း "{task_title}" ကာလကျော်လွန်သွားပါပြီ (နောက်ဆုံးရက်: {due_date})။ အမြန်ဆုံးပြီးမြောက်အောင်ဆောင်ရွက်ပါ။',
            'due_today': f'သင်၏လုပ်ငန်း "{task_title}" ကို ယနေ့ ပြီးမြောက်အောင် ဆောင်ရွက်ရမည်ဖြစ်ပါသည်။ မမေ့ပါနှင့်။',
            'due_soon': f'သင်၏လုပ်ငန်း "{task_title}" သည် {days_left} ရက်အကြာတွင် သက်တမ်းကုန်ဆုံးပါမည် (နောက်ဆုံးရက်: {due_date})။',
        },
    }
    return templates.get(lang, templates[''])[kind]


def render_due_email(lang, student_name, message):
    """回傳 (subject, body)，body 中會內嵌已翻譯好的 message。"""
    templates = {
        '': {
            'subject': '【ReadyTo Taiwan 提醒】您的任務狀態提醒',
            'body': (
                f'{student_name} 您好，\n\n'
                f'{message}\n\n'
                f'請登入系統完成您的任務！\n\n'
                f'ReadyTo Taiwan 團隊\n\n'
                f'*本信件為系統自動發送，請勿回覆。'
            ),
        },
        'en': {
            'subject': '[ReadyTo Taiwan] Task Reminder Notification',
            'body': (
                f'Hello {student_name},\n\n'
                f'{message}\n\n'
                f'Please log in to the system to complete your task!\n\n'
                f'ReadyTo Taiwan Team\n\n'
                f'*This email was sent automatically by the system; please do not reply.'
            ),
        },
        'vi': {
            'subject': '[ReadyTo Taiwan] Thông báo nhắc nhở nhiệm vụ',
            'body': (
                f'Xin chào {student_name},\n\n'
                f'{message}\n\n'
                f'Vui lòng đăng nhập vào hệ thống để hoàn thành nhiệm vụ của bạn!\n\n'
                f'Đội ngũ ReadyTo Taiwan\n\n'
                f'*Email này được hệ thống tự động gửi, vui lòng không trả lời.'
            ),
        },
        'id': {
            'subject': '[ReadyTo Taiwan] Pemberitahuan Pengingat Tugas',
            'body': (
                f'Halo {student_name},\n\n'
                f'{message}\n\n'
                f'Silakan masuk ke sistem untuk menyelesaikan tugas Anda!\n\n'
                f'Tim ReadyTo Taiwan\n\n'
                f'*Email ini dikirim secara otomatis oleh sistem, mohon tidak membalas.'
            ),
        },
        'ms': {
            'subject': '[ReadyTo Taiwan] Notifikasi Peringatan Tugasan',
            'body': (
                f'Salam {student_name},\n\n'
                f'{message}\n\n'
                f'Sila log masuk ke sistem untuk menyelesaikan tugasan anda!\n\n'
                f'Pasukan ReadyTo Taiwan\n\n'
                f'*E-mel ini dihantar secara automatik oleh sistem, sila jangan balas.'
            ),
        },
        'th': {
            'subject': '[ReadyTo Taiwan] การแจ้งเตือนงาน',
            'body': (
                f'สวัสดีคุณ {student_name},\n\n'
                f'{message}\n\n'
                f'กรุณาเข้าสู่ระบบเพื่อดำเนินงานให้เสร็จสมบูรณ์!\n\n'
                f'ทีมงาน ReadyTo Taiwan\n\n'
                f'*อีเมลนี้ถูกส่งโดยระบบอัตโนมัติ กรุณาอย่าตอบกลับ'
            ),
        },
        'ja': {
            'subject': '[ReadyTo Taiwan] タスクリマインダー通知',
            'body': (
                f'{student_name} 様\n\n'
                f'{message}\n\n'
                f'システムにログインしてタスクを完了してください！\n\n'
                f'ReadyTo Taiwan チーム\n\n'
                f'※本メールはシステムより自動送信されています。返信はご遠慮ください。'
            ),
        },
        'ko': {
            'subject': '[ReadyTo Taiwan] 작업 알림',
            'body': (
                f'{student_name}님, 안녕하세요.\n\n'
                f'{message}\n\n'
                f'시스템에 로그인하여 작업을 완료해 주세요!\n\n'
                f'ReadyTo Taiwan 팀\n\n'
                f'*본 메일은 시스템에서 자동으로 발송되었습니다. 회신하지 마세요.'
            ),
        },
        'my': {
            'subject': '[ReadyTo Taiwan] လုပ်ငန်းသတိပေးချက်',
            'body': (
                f'{student_name} ခင်ဗျား/ရှင်၊\n\n'
                f'{message}\n\n'
                f'သင့်လုပ်ငန်းကို ပြီးမြောက်အောင် စနစ်ထဲသို့ လော့ဂ်အင်ဝင်ပါ!\n\n'
                f'ReadyTo Taiwan အဖွဲ့\n\n'
                f'*ဤအီးမေးလ်ကို စနစ်မှ အလိုအလျောက် ပေးပို့ထားခြင်းဖြစ်ပါသည်၊ ပြန်လည်မဖြေကြားပါနှင့်။'
            ),
        },
    }
    t = templates.get(lang, templates[''])
    return t['subject'], t['body']


def render_skipped_message(lang, task_title, skipped_titles):
    """跳過前置任務提醒。skipped_titles 是完整清單（未截斷），本函式內部只顯示前 3 筆並附上剩餘數量。"""
    shown = skipped_titles[:3]
    extra = len(skipped_titles) - 3

    if lang == 'en':
        skipped_str = ", ".join([f'"{t}"' for t in shown])
        if extra > 0:
            skipped_str += f" and {extra} other tasks"
        return f'You have completed "{task_title}", but the prior task(s) {skipped_str} is/are not yet completed. It is recommended to complete them in order!'
    elif lang == 'vi':
        skipped_str = ", ".join([f'"{t}"' for t in shown])
        if extra > 0:
            skipped_str += f" và {extra} nhiệm vụ khác"
        return f'Bạn đã hoàn thành "{task_title}", nhưng (các) nhiệm vụ trước đó {skipped_str} chưa được hoàn thành. Khuyên bạn nên hoàn thành chúng theo thứ tự!'
    elif lang == 'id':
        skipped_str = ", ".join([f'"{t}"' for t in shown])
        if extra > 0:
            skipped_str += f" dan {extra} tugas lainnya"
        return f'Anda telah menyelesaikan "{task_title}", tetapi tugas sebelumnya {skipped_str} belum diselesaikan. Disarankan untuk menyelesaikannya secara berurutan!'
    elif lang == 'ms':
        skipped_str = ", ".join([f'"{t}"' for t in shown])
        if extra > 0:
            skipped_str += f" dan {extra} tugasan lain"
        return f'Anda telah menyelesaikan "{task_title}", tetapi tugasan sebelumnya {skipped_str} belum selesai. Disyorkan untuk menyelesaikannya mengikut urutan!'
    elif lang == 'th':
        skipped_str = ", ".join([f'"{t}"' for t in shown])
        if extra > 0:
            skipped_str += f" และอีก {extra} งาน"
        return f'คุณได้ทำ "{task_title}" เสร็จสิ้นแล้ว แต่งานก่อนหน้า {skipped_str} ยังไม่เสร็จสมบูรณ์ ขอแนะนำให้ทำตามลำดับ!'
    elif lang == 'ja':
        skipped_str = "、".join([f'「{t}」' for t in shown])
        if extra > 0:
            skipped_str += f" など計 {len(skipped_titles)} 件のタスク"
        return f'「{task_title}」を完了しましたが、前置タスク{skipped_str}が未完了です。順序通りに完了することをお勧めします！'
    elif lang == 'ko':
        skipped_str = ", ".join([f'"{t}"' for t in shown])
        if extra > 0:
            skipped_str += f" 등 총 {len(skipped_titles)}개 작업"
        return f'"{task_title}"을(를) 완료했으나, 이전 작업인 {skipped_str}이(가) 아직 완료되지 않았습니다. 순서대로 완료하는 것을 권장합니다!'
    elif lang == 'my':
        skipped_str = ", ".join([f'"{t}"' for t in shown])
        if extra > 0:
            skipped_str += f" နှင့် အခြား {extra} ခု"
        return f'သင်သည် "{task_title}" ကို ပြီးမြောက်ပြီးဖြစ်သော်လည်း ယခင်လုပ်ဆောင်ရမည့် {skipped_str} မပြီးသေးပါ။ အစီအစဉ်အတိုင်း လုပ်ဆောင်ရန် အကြံပြုပါသည်!'
    else:  # zh-hant
        skipped_str = "、".join([f"「{t}」" for t in shown])
        if extra > 0:
            skipped_str += f" 等共 {len(skipped_titles)} 個任務"
        return f"您已完成「{task_title}」，但前置任務 {skipped_str} 尚未完成，建議您依序完成！"

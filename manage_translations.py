import os
import re

BASE_DIR = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'
LANGS = ['en', 'vi', 'id', 'ms', 'th', 'my', 'ko', 'ja']

# 集中管理所有手動翻譯的字串
TRANSLATIONS = {
    'en': {
        "必做": "Required", "建議": "Suggested", "小貼士": "Tips",
        "首頁": "Home", "儀表板": "Dashboard", "留學流程": "Study Flow",
        "任務清單": "Task List", "資訊中心": "Info Center", "學長姐分享": "Alumni Sharing",
        "常見問題": "FAQ", "詢問AI小幫手": "Ask AI", "登出": "Logout", "開始流程": "Start"
    },
    'vi': {
        "必做": "Bắt buộc", "建議": "Đề xuất", "小貼士": "Mẹo nhỏ",
        "首頁": "Trang chủ", "儀表板": "Bảng điều khiển", "留學流程": "Quy trình du học",
        "任務清單": "Danh sách nhiệm vụ", "資訊中心": "Trung tâm thông tin", "學長姐分享": "Chia sẻ cựu sinh viên",
        "常見問題": "Câu hỏi thường gặp", "詢問AI小幫手": "Hỏi AI", "登出": "Đăng xuất", "開始流程": "Bắt đầu"
    },
    'id': {
        "必做": "Wajib", "建議": "Disarankan", "小貼士": "Tips",
        "首頁": "Beranda", "儀表板": "Dasbor", "留學流程": "Proses Belajar",
        "任務清單": "Daftar Tugas", "資訊中心": "Pusat Info", "學長姐分享": "Berbagi Alumni",
        "常見問題": "FAQ", "詢問AI小幫手": "Tanya AI", "登出": "Keluar", "開始流程": "Mulai"
    },
    'ms': {
        "必做": "Wajib", "建議": "Dicadangkan", "小貼士": "Tips",
        "首頁": "Utama", "儀表板": "Papan Pemuka", "留學流程": "Proses Belajar",
        "任務清單": "Senarai Tugas", "資訊中心": "Pusat Maklumat", "學長姐分享": "Perkongsian Alumni",
        "常見問題": "Soalan Lazim", "詢問AI小幫手": "Tanya AI", "登出": "Log Keluar", "開始流程": "Mula"
    },
    'th': {
        "必做": "จำเป็น", "建議": "แนะนำ", "小貼士": "เคล็ดลับ",
        "首頁": "หน้าแรก", "儀表板": "แดชบอร์ด", "留學流程": "ขั้นตอนการศึกษา",
        "任務清單": "รายการงาน", "資訊中心": "ศูนย์ข้อมูล", "學長姐分享": "ศิษย์เก่าแบ่งปัน",
        "常見問題": "คำถามที่พบบ่อย", "詢問AI小幫手": "ถาม AI", "登出": "ออกจากระบบ", "開始流程": "เริ่มกระบวนการ"
    },
    'my': {
        "必做": "မဖြစ်မနေလုပ်ရမည်", "建議": "အကြံပြုထားသည်", "小貼士": "အကြံပြုချက်များ",
        "首頁": "ပင်မစာမျက်နှာ", "儀表板": "ဒက်ရှ်ဘုတ်", "留學流程": "လေ့လာမှုလုပ်ငန်းစဉ်",
        "任務清單": "အလုပ်စာရင်း", "資訊中心": "သတင်းအချက်အလက်ဗဟိုဌာန", "學長姐分享": "ကျောင်းသားဟောင်းဝေမျှခြင်း",
        "常見問題": "အမေးများသောမေးခွန်းများ", "詢問AI小幫手": "AI ကိုမေးပါ", "登出": "ထွက်ရန်", "開始流程": "စတင်ပါ"
    },
    'ko': {
        "必做": "필수", "建議": "권장", "小貼士": "팁",
        "首頁": "홈", "儀表板": "대시보드", "留學流程": "유학 절차",
        "任務清單": "작업 목록", "資訊中心": "정보 센터", "學長姐分享": "선배 공유",
        "常見問題": "자주 묻는 질문", "詢問AI小幫手": "AI 도우미", "登出": "로그아웃", "開始流程": "시작하기"
    },
    'ja': {
        "必做": "必須", "建議": "推奨", "小貼士": "ヒント",
        "首頁": "ホーム", "儀表板": "ダッシュボード", "留學流程": "留学プロセス",
        "任務清單": "タスクリスト", "資訊中心": "情報センター", "學長姐分享": "先輩の体験談",
        "常見問題": "よくある質問", "詢問AI小幫手": "AIアシスタント", "登出": "ログアウト", "開始流程": "開始する"
    }
}

def update_translations():
    """
    1. 遍歷所有語言的 django.po
    2. 自動移除字典中字串的 `#, fuzzy` 標籤
    3. 自動寫入或更新翻譯
    """
    for lang in LANGS:
        po_path = os.path.join(BASE_DIR, lang, 'LC_MESSAGES', 'django.po')
        if not os.path.exists(po_path):
            continue
            
        with open(po_path, 'r', encoding='utf-8') as f:
            content = f.read()

        strings_to_update = TRANSLATIONS[lang]
        
        for zh_str, target_str in strings_to_update.items():
            # 移除可能會干擾編譯的 fuzzy 標籤
            content = re.sub(r'#, fuzzy\n(#\| msgid ".*?"\n)?msgid "' + zh_str + '"', 'msgid "' + zh_str + '"', content)
            
            # 更新或新增翻譯
            if f'msgid "{zh_str}"' not in content:
                content += f'\nmsgid "{zh_str}"\nmsgstr "{target_str}"\n'
            else:
                content = re.sub(f'msgid "{zh_str}"\nmsgstr ".*?"', f'msgid "{zh_str}"\nmsgstr "{target_str}"', content)
                
        with open(po_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✅ Successfully updated and cleaned {lang} translations.')

if __name__ == '__main__':
    update_translations()
    print("\n執行完畢！請記得在終端機執行 `python manage.py compilemessages`")

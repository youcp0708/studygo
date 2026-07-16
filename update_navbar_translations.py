import os, re

base = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'
langs = ['en', 'vi', 'id', 'ms', 'th', 'my', 'ko', 'ja']

strings = [
    "首頁", "儀表板", "留學流程", "任務清單", "資訊中心", "學長姐分享", "常見問題", "詢問AI小幫手", "登出", "開始流程"
]

translations = {
    'en': {
        "首頁": "Home",
        "儀表板": "Dashboard",
        "留學流程": "Study Flow",
        "任務清單": "Task List",
        "資訊中心": "Info Center",
        "學長姐分享": "Alumni Sharing",
        "常見問題": "FAQ",
        "詢問AI小幫手": "Ask AI",
        "登出": "Logout",
        "開始流程": "Start"
    },
    'vi': {
        "首頁": "Trang chủ",
        "儀表板": "Bảng điều khiển",
        "留學流程": "Quy trình du học",
        "任務清單": "Danh sách nhiệm vụ",
        "資訊中心": "Trung tâm thông tin",
        "學長姐分享": "Chia sẻ cựu sinh viên",
        "常見問題": "Câu hỏi thường gặp",
        "詢問AI小幫手": "Hỏi AI",
        "登出": "Đăng xuất",
        "開始流程": "Bắt đầu"
    },
    'id': {
        "首頁": "Beranda",
        "儀表板": "Dasbor",
        "留學流程": "Proses Belajar",
        "任務清單": "Daftar Tugas",
        "資訊中心": "Pusat Info",
        "學長姐分享": "Berbagi Alumni",
        "常見問題": "FAQ",
        "詢問AI小幫手": "Tanya AI",
        "登出": "Keluar",
        "開始流程": "Mulai"
    },
    'ms': {
        "首頁": "Utama",
        "儀表板": "Papan Pemuka",
        "留學流程": "Proses Belajar",
        "任務清單": "Senarai Tugas",
        "資訊中心": "Pusat Maklumat",
        "學長姐分享": "Perkongsian Alumni",
        "常見問題": "Soalan Lazim",
        "詢問AI小幫手": "Tanya AI",
        "登出": "Log Keluar",
        "開始流程": "Mula"
    },
    'th': {
        "首頁": "หน้าแรก",
        "儀表板": "แดชบอร์ด",
        "留學流程": "ขั้นตอนการศึกษา",
        "任務清單": "รายการงาน",
        "資訊中心": "ศูนย์ข้อมูล",
        "學長姐分享": "ศิษย์เก่าแบ่งปัน",
        "常見問題": "คำถามที่พบบ่อย",
        "詢問AI小幫手": "ถาม AI",
        "登出": "ออกจากระบบ",
        "開始流程": "เริ่มกระบวนการ"
    },
    'my': {
        "首頁": "ပင်မစာမျက်နှာ",
        "儀表板": "ဒက်ရှ်ဘုတ်",
        "留學流程": "လေ့လာမှုလုပ်ငန်းစဉ်",
        "任務清單": "အလုပ်စာရင်း",
        "資訊中心": "သတင်းအချက်အလက်ဗဟိုဌာန",
        "學長姐分享": "ကျောင်းသားဟောင်းဝေမျှခြင်း",
        "常見問題": "အမေးများသောမေးခွန်းများ",
        "詢問AI小幫手": "AI ကိုမေးပါ",
        "登出": "ထွက်ရန်",
        "開始流程": "စတင်ပါ"
    },
    'ko': {
        "首頁": "홈",
        "儀表板": "대시보드",
        "留學流程": "유학 절차",
        "任務清單": "작업 목록",
        "資訊中心": "정보 센터",
        "學長姐分享": "선배 공유",
        "常見問題": "자주 묻는 질문",
        "詢問AI小幫手": "AI 도우미",
        "登出": "로그아웃",
        "開始流程": "시작하기"
    },
    'ja': {
        "首頁": "ホーム",
        "儀表板": "ダッシュボード",
        "留學流程": "留学プロセス",
        "任務清單": "タスクリスト",
        "資訊中心": "情報センター",
        "學長姐分享": "先輩の体験談",
        "常見問題": "よくある質問",
        "詢問AI小幫手": "AIアシスタント",
        "登出": "ログアウト",
        "開始流程": "開始する"
    }
}

for lang in langs:
    po_path = os.path.join(base, lang, 'LC_MESSAGES', 'django.po')
    if not os.path.exists(po_path): continue
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    for zh_str in strings:
        # Check if exists
        target = translations[lang][zh_str]
        
        # Remove fuzzy for this specific msgid
        content = re.sub(r'#, fuzzy\n(#\| msgid ".*?"\n)?msgid "' + zh_str + '"', 'msgid "' + zh_str + '"', content)
        
        if f'msgid "{zh_str}"' not in content:
            content += f'\nmsgid "{zh_str}"\nmsgstr "{target}"\n'
        else:
            # Replace empty or old translation
            content = re.sub(f'msgid "{zh_str}"\nmsgstr ".*?"', f'msgid "{zh_str}"\nmsgstr "{target}"', content)
            
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'Updated navbar translations for {lang}')

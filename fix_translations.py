import os, re

base = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'

translations = {
    'en': {'Tips': 'Tips', 'Required': 'Required', 'Suggested': 'Suggested'},
    'vi': {'Tips': 'Mẹo nhỏ', 'Required': 'Bắt buộc', 'Suggested': 'Đề xuất'},
    'id': {'Tips': 'Tips', 'Required': 'Wajib', 'Suggested': 'Disarankan'},
    'ms': {'Tips': 'Petua', 'Required': 'Wajib', 'Suggested': 'Dicadangkan'},
    'th': {'Tips': 'เคล็ดลับ', 'Required': 'จำเป็น', 'Suggested': 'แนะนำ'},
    'my': {'Tips': 'အကြံပြုချက်များ', 'Required': 'မဖြစ်မနေလုပ်ရမည်', 'Suggested': 'အကြံပြုထားသည်'},
    'ko': {'Tips': '팁', 'Required': '필수', 'Suggested': '권장'},
    'ja': {'Tips': 'ヒント', 'Required': '必須', 'Suggested': '推奨'}
}

for lang, tr in translations.items():
    po_path = os.path.join(base, lang, 'LC_MESSAGES', 'django.po')
    if os.path.exists(po_path):
        with open(po_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace 小貼士 (Tips)
        if 'msgid "小貼士"' in content:
            content = re.sub(r'msgid "小貼士"\nmsgstr ".*?"', f'msgid "小貼士"\nmsgstr "{tr["Tips"]}"', content)
        
        # Replace 必做 (Required)
        if 'msgid "必做"' in content:
            content = re.sub(r'msgid "必做"\nmsgstr ".*?"', f'msgid "必做"\nmsgstr "{tr["Required"]}"', content)
            
        # Replace 建議 (Suggested)
        if 'msgid "建議"' in content:
            content = re.sub(r'msgid "建議"\nmsgstr ".*?"', f'msgid "建議"\nmsgstr "{tr["Suggested"]}"', content)
            
        with open(po_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed {lang}')

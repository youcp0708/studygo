import os, re

base = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'

translations = {
    'en': 'Tips',
    'vi': 'Mẹo nhỏ',
    'id': 'Tips',
    'ms': 'Petua',
    'th': 'เคล็ดลับ',
    'my': 'အကြံပြုချက်များ',
    'ko': '팁',
    'ja': 'ヒント'
}

for lang, tip_str in translations.items():
    po_path = os.path.join(base, lang, 'LC_MESSAGES', 'django.po')
    if os.path.exists(po_path):
        with open(po_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'msgid "小貼士"' in content:
            # Replace the msgstr for 小貼士
            content = re.sub(r'msgid "小貼士"\nmsgstr ".*?"', f'msgid "小貼士"\nmsgstr "{tip_str}"', content)
            
            with open(po_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed {lang}')

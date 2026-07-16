import os, re

base = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'

translations = {
    'en': {'Required': 'Required', 'Suggested': 'Suggested'},
    'vi': {'Required': 'Bắt buộc', 'Suggested': 'Đề xuất'},
    'id': {'Required': 'Wajib', 'Suggested': 'Disarankan'},
    'ms': {'Required': 'Wajib', 'Suggested': 'Dicadangkan'},
    'th': {'Required': 'จำเป็น', 'Suggested': 'แนะนำ'},
    'my': {'Required': 'မဖြစ်မနေလုပ်ရမည်', 'Suggested': 'အကြံပြုထားသည်'},
    'ko': {'Required': '필수', 'Suggested': '권장'},
    'ja': {'Required': '必須', 'Suggested': '推奨'}
}

for lang, tr in translations.items():
    po_path = os.path.join(base, lang, 'LC_MESSAGES', 'django.po')
    if not os.path.exists(po_path):
        continue
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Ensure msgid for 必做
    if 'msgid "必做"' not in content:
        content += f"\nmsgid \"必做\"\nmsgstr \"{tr['Required']}\"\n"
    else:
        # replace existing
        content = re.sub(r'msgid "必做"\nmsgstr ".*?"', f'msgid "必做"\nmsgstr "{tr["Required"]}"', content)
    # Ensure msgid for 建議
    if 'msgid "建議"' not in content:
        content += f"\nmsgid \"建議\"\nmsgstr \"{tr['Suggested']}\"\n"
    else:
        content = re.sub(r'msgid "建議"\nmsgstr ".*?"', f'msgid "建議"\nmsgstr "{tr["Suggested"]}"', content)
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Updated {lang}')

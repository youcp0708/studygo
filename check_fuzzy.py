import os

base = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'
for lang in ['en', 'vi', 'id', 'ms', 'th', 'my', 'ko', 'ja']:
    po_path = os.path.join(base, lang, 'LC_MESSAGES', 'django.po')
    if not os.path.exists(po_path): continue
    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if 'msgid "必做"' in line or 'msgid "小貼士"' in line or 'msgid "建議"' in line:
            print(f'[{lang}] Found {line.strip()} at line {i}')
            if i > 0 and 'fuzzy' in lines[i-1]:
                print(f'   -> FUZZY! Prev line: {lines[i-1].strip()}')
            if i > 0 and 'fuzzy' in lines[i-2]:
                print(f'   -> FUZZY (2)! Prev line: {lines[i-2].strip()}')

import os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'
for lang in ['vi', 'th', 'ms', 'my', 'ko', 'ja', 'id', 'en']:
    po = os.path.join(base, lang, 'LC_MESSAGES', 'django.po')
    if os.path.exists(po):
        with open(po, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if 'msgid \"任務完成率\"' in line:
                    print(lang + ':', lines[i+1].strip())

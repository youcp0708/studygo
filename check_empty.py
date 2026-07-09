import os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'
for lang in ['vi', 'th', 'ms', 'my', 'ko', 'ja', 'id', 'en']:
    po = os.path.join(base, lang, 'LC_MESSAGES', 'django.po')
    if os.path.exists(po):
        with open(po, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'msgid \"任務完成率\"\nmsgstr \"\"' in content:
            print(lang, '任務完成率 EMPTY')
        if 'msgid \"小貼士\"\nmsgstr \"\"' in content:
            print(lang, '小貼士 EMPTY')
        if 'msgid \"完成\"\nmsgstr \"\"' in content:
            print(lang, '完成 EMPTY')


import os, re

base = r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale'
for lang in ['en', 'vi', 'id', 'ms', 'th', 'my', 'ko', 'ja']:
    po_path = os.path.join(base, lang, 'LC_MESSAGES', 'django.po')
    if not os.path.exists(po_path): continue
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Sometimes there's a comment between fuzzy and msgid, e.g.
    # #, fuzzy
    # #| msgid "..."
    # msgid "必做"
    
    # We will just remove the '#, fuzzy\n' lines completely everywhere to be safe,
    # OR we can just remove it specifically for our keys by doing a regex that removes '#, fuzzy' 
    # block before our msgids.
    
    # Since compilemessages ignores ANY fuzzy strings, and we want to ensure our translations work,
    # we can remove '#, fuzzy\n' specifically above our keys.
    
    # Let's remove the fuzzy line if it appears before 小貼士
    content = re.sub(r'#, fuzzy\n(#\| msgid ".*?"\n)?msgid "小貼士"', 'msgid "小貼士"', content)
    
    # Let's remove the fuzzy line if it appears before 必做
    content = re.sub(r'#, fuzzy\n(#\| msgid ".*?"\n)?msgid "必做"', 'msgid "必做"', content)
    
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'Removed fuzzy from {lang}')

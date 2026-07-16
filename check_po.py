import re
with open(r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale\en\LC_MESSAGES\django.po', 'r', encoding='utf-8') as f:
    content = f.read()

def check(msgid):
    if f'msgid "{msgid}"' not in content:
        print(f'{msgid} NOT FOUND')
        return
    m = re.search(f'msgid "{msgid}"\nmsgstr "(.*?)"', content)
    if m:
        print(f'{msgid} -> {m.group(1)}')
    else:
        print(f'{msgid} FOUND BUT MSGSTR NO MATCH (maybe multiline?)')

check("小貼士")
check("必做")
check("建議")

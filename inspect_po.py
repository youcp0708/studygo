import re
with open(r'c:\Users\Shwe Thinzar Oo\Downloads\studygo\locale\en\LC_MESSAGES\django.po', 'r', encoding='utf-8') as f:
    content = f.read()

def print_block(msgid):
    idx = content.find('msgid "' + msgid + '"')
    if idx != -1:
        print('--- ' + msgid + ' ---')
        end = content.find('\n\n', idx)
        if end == -1: end = len(content)
        block = content[idx:end]
        print(block.encode('unicode_escape').decode('ascii'))

print_block('小貼士')
print_block('必做')
print_block('建議')

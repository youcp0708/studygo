# -*- coding: utf-8 -*-
import polib, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def resolve_conflicts(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()
    if '<<<<<<<' not in content:
        return 0

    lines = content.split('\n')
    out = []
    i = 0
    conflicts = 0
    while i < len(lines):
        if lines[i].startswith('<<<<<<<'):
            conflicts += 1
            head_lines = []
            theirs_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('======='):
                head_lines.append(lines[i])
                i += 1
            i += 1
            while i < len(lines) and not lines[i].startswith('>>>>>>>'):
                theirs_lines.append(lines[i])
                i += 1
            i += 1

            def has_content(ls):
                return any(l.startswith('msgid ') or l.startswith('msgstr ') or (l.startswith('"') and l.strip() != '""') for l in ls)
            def has_filled_msgstr(ls):
                return any(l.startswith('msgstr "') and l.strip() not in ('msgstr ""', 'msgstr ""') and len(l.strip()) > 9 for l in ls)

            if not has_content(theirs_lines) and has_content(head_lines):
                out.extend(head_lines)
            elif not has_filled_msgstr(theirs_lines) and has_filled_msgstr(head_lines):
                out.extend(head_lines)
            else:
                out.extend(theirs_lines)
        else:
            out.append(lines[i])
            i += 1

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    return conflicts

langs = ['en', 'vi', 'id', 'ms', 'th', 'ja', 'ko', 'my']
for lang in langs:
    path = f'locale/{lang}/LC_MESSAGES/django.po'
    n = resolve_conflicts(path)
    if n == 0:
        print(f'{lang}: no conflicts')
        continue
    try:
        po = polib.pofile(path)
        po.save_as_mofile(path.replace('.po', '.mo'))
        print(f'{lang}: resolved {n} conflicts, compiled OK ({len(po)} entries)')
    except Exception as e:
        print(f'{lang}: ERROR after resolve — {e}')

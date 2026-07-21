# -*- coding: utf-8 -*-
"""
Resolve git merge conflicts in .po files.
For #: comment-only conflicts: keep 'theirs' (new/16).
For msgid/msgstr conflicts: keep 'theirs' (newer) if it has content, else keep HEAD.
"""

def resolve(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()

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
            i += 1  # skip =======
            while i < len(lines) and not lines[i].startswith('>>>>>>>'):
                theirs_lines.append(lines[i])
                i += 1
            i += 1  # skip >>>>>>>

            def has_real_content(ls):
                return any(l.startswith('msgid ') or l.startswith('msgstr ') or l.startswith('"') for l in ls)

            def has_nonempty_msgstr(ls):
                for l in ls:
                    if l.startswith('msgstr "') and l.strip() != 'msgstr ""':
                        return True
                return False

            # Always prefer theirs; only fall back to head if theirs is empty/comment-only
            if not has_real_content(theirs_lines) and has_real_content(head_lines):
                out.extend(head_lines)
            elif has_real_content(theirs_lines) and not has_nonempty_msgstr(theirs_lines) and has_nonempty_msgstr(head_lines):
                # theirs has empty msgstr, head has content → keep head
                out.extend(head_lines)
            else:
                # default: keep theirs
                out.extend(theirs_lines)
        else:
            out.append(lines[i])
            i += 1

    result = '\n'.join(out)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f'Resolved {conflicts} conflicts in {path}')

resolve('locale/en/LC_MESSAGES/django.po')

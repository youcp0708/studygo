import os
import sys
import polib
from deep_translator import GoogleTranslator

sys.stdout.reconfigure(encoding='utf-8')

LANGUAGES = {
    'en': 'en',
    'id': 'id',
    'ja': 'ja',
    'ms': 'ms',
    'my': 'my',
    'th': 'th',
    'ko': 'ko',
}

locale_dir = r"c:\studygo\locale"

for lang, target_lang in LANGUAGES.items():
    po_path = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.po')
    mo_path = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.mo')
    if os.path.exists(po_path):
        po = polib.pofile(po_path)
        modified = False
        translator = GoogleTranslator(source='zh-TW', target=target_lang)
        
        # Ensure target strings exist
        targets = ['未讀通知', '即將到期任務']
        existing_msgids = [entry.msgid for entry in po]
        for t in targets:
            if t not in existing_msgids:
                entry = polib.POEntry(msgid=t, msgstr='')
                po.append(entry)
                modified = True

        
        for entry in po:
            needs_translation = False
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
                # If it's fuzzy, the msgstr is likely wrong, so clear it
                entry.msgstr = ''
                needs_translation = True
                
            if not entry.msgstr:
                needs_translation = True
                
            if needs_translation:
                try:
                    translated = translator.translate(entry.msgid)
                    if translated:
                        entry.msgstr = translated
                        modified = True
                        print(f"[{lang}] {entry.msgid} -> {translated}")
                except Exception as e:
                    print(f"[{lang}] Error translating {entry.msgid}: {e}")
                    
        if modified:
            po.save()
            po.save_as_mofile(mo_path)
            print(f"[{lang}] Compiled .mo file.")

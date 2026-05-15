import os
import sys
import polib
from deep_translator import GoogleTranslator

# Fix stdout encoding for Windows
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
        
        for entry in po:
            needs_translation = False
            
            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')
                needs_translation = True
                
            if not entry.msgstr:
                needs_translation = True
                
            if needs_translation:
                try:
                    translated = translator.translate(entry.msgid)
                    if translated:
                        entry.msgstr = translated
                        modified = True
                        print(f"[{lang}] Translated: {entry.msgid} -> {translated}")
                except Exception as e:
                    print(f"[{lang}] Error translating {entry.msgid}: {e}")
                    
        if modified:
            po.save()
            po.save_as_mofile(mo_path)
            print(f"[{lang}] Saved and compiled .mo file.")

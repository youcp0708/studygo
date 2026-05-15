import os
import re
import polib
from deep_translator import GoogleTranslator

# Languages and their codes in deep-translator
LANGUAGES = {
    'en': 'en',
    'id': 'id',
    'ja': 'ja',
    'ms': 'ms',
    'my': 'my', # Myanmar (Burmese)
    'th': 'th',
    'ko': 'ko',
}

def extract_strings(root_dir):
    strings = set()
    
    # Regex for {% trans "..." %} and _("...")
    re_trans_tag = re.compile(r'{%\s*trans\s+["\']([^"\']+)["\']\s*%}')
    re_gettext = re.compile(r'_\(["\']([^"\']+)["\']\)')
    
    for subdir, _, files in os.walk(root_dir):
        if 'venv' in subdir or '.git' in subdir or 'locale' in subdir:
            continue
        for f in files:
            if f.endswith('.html') or f.endswith('.py'):
                filepath = os.path.join(subdir, f)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                        strings.update(re_trans_tag.findall(content))
                        strings.update(re_gettext.findall(content))
                except Exception as e:
                    pass
    return strings

def update_po_files():
    project_dir = r"c:\studygo"
    locale_dir = os.path.join(project_dir, 'locale')
    
    # 1. Extract all strings from code
    extracted_strings = extract_strings(project_dir)
    print(f"Found {len(extracted_strings)} translatable strings in project.")
    
    for lang_code, target_lang in LANGUAGES.items():
        po_path = os.path.join(locale_dir, lang_code, 'LC_MESSAGES', 'django.po')
        mo_path = os.path.join(locale_dir, lang_code, 'LC_MESSAGES', 'django.mo')
        
        if not os.path.exists(po_path):
            print(f"Skipping {lang_code}, PO file not found.")
            continue
            
        po = polib.pofile(po_path)
        existing_msgids = [entry.msgid for entry in po]
        
        # Add missing strings to PO
        added = 0
        for s in extracted_strings:
            if s not in existing_msgids:
                entry = polib.POEntry(
                    msgid=s,
                    msgstr='',
                )
                po.append(entry)
                added += 1
                
        print(f"[{lang_code}] Added {added} new strings.")
        
        # Translate empty msgstrs
        translated_count = 0
        translator = GoogleTranslator(source='zh-TW', target=target_lang)
        
        for entry in po:
            if not entry.msgstr:
                try:
                    translated = translator.translate(entry.msgid)
                    if translated:
                        entry.msgstr = translated
                        translated_count += 1
                except Exception as e:
                    print(f"[{lang_code}] Error translating '{entry.msgid}': {e}")
                    
        print(f"[{lang_code}] Translated {translated_count} empty strings.")
        
        # Save PO and compile to MO using polib!
        po.save()
        po.save_as_mofile(mo_path)
        print(f"[{lang_code}] Compiled .mo file successfully.")

if __name__ == '__main__':
    update_po_files()

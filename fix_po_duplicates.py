from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parent
LOCALE_DIR = BASE_DIR / "locale"


def get_msgid(entry: str):
    match = re.search(r'^msgid\s+(".*")', entry, flags=re.MULTILINE)
    if not match:
        return None

    # 不處理 header: msgid ""
    if match.group(1) == '""':
        return None

    return match.group(1)


def get_msgstr(entry: str):
    match = re.search(r'^msgstr\s+(".*")', entry, flags=re.MULTILINE)
    if not match:
        return ""
    return match.group(1)


def replace_msgstr(entry: str, new_msgstr: str):
    return re.sub(
        r'^msgstr\s+".*"',
        f'msgstr {new_msgstr}',
        entry,
        count=1,
        flags=re.MULTILINE
    )


def clean_po_file(po_path: Path):
    text = po_path.read_text(encoding="utf-8")

    # 以空白行切成一個一個翻譯區塊
    entries = re.split(r'\n\s*\n', text)

    seen = {}
    cleaned = []
    removed_count = 0
    updated_count = 0

    for entry in entries:
        msgid = get_msgid(entry)

        # 沒有 msgid 的區塊直接保留
        if not msgid:
            cleaned.append(entry)
            continue

        msgstr = get_msgstr(entry)

        if msgid not in seen:
            seen[msgid] = len(cleaned)
            cleaned.append(entry)
        else:
            # 如果前面的 msgstr 是空的，而後面重複的 msgstr 有內容，就把翻譯補回前面那組
            first_index = seen[msgid]
            first_entry = cleaned[first_index]
            first_msgstr = get_msgstr(first_entry)

            if first_msgstr == '""' and msgstr != '""':
                cleaned[first_index] = replace_msgstr(first_entry, msgstr)
                updated_count += 1

            removed_count += 1

    backup_path = po_path.with_suffix(".po.bak")
    backup_path.write_text(text, encoding="utf-8")

    po_path.write_text("\n\n".join(cleaned).rstrip() + "\n", encoding="utf-8")

    print(f"Fixed: {po_path}")
    print(f"  removed duplicates: {removed_count}")
    print(f"  filled empty msgstr: {updated_count}")
    print(f"  backup: {backup_path}")


def main():
    po_files = list(LOCALE_DIR.glob("*/LC_MESSAGES/django.po"))

    if not po_files:
        print("No django.po files found.")
        return

    for po_path in po_files:
        clean_po_file(po_path)


if __name__ == "__main__":
    main()
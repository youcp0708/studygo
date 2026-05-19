import re

with open("locale/en/LC_MESSAGES/django.po", encoding="utf-8") as f:
    content = f.read()

msgids = set()
for m in re.finditer(r'^msgid "(.+?)"', content, re.MULTILINE):
    msgids.add(m.group(1))
for m in re.finditer(r'^msgid ""\n((?:"[^"]*"\n)+)', content, re.MULTILINE):
    parts = re.findall(r'"([^"]*)"', m.group(1))
    msgids.add("".join(parts))

check = [
    "必要", "視情況", "規費", "外來人士在台生活諮詢", "健康檢查合格證明",
    "30 天內", "15 天", "返回資訊中心", "相關資源", "辦理外僑居留證（ARC）",
    "辦理重點一覽", "外籍生辦理居留證（ARC）",
]
for s in check:
    print(f"{'✓' if s in msgids else '✗'} {s!r}")

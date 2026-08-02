"""
chatbot/knowledge_data/schools.py

「學校資訊」分類的知識庫內容：把每一所已查核學校的校務資料，
整理成一則可被 RAG 檢索的知識條目（category='school_info'，university=該校）。

School / SchoolUnit 資料表提供的是「結構化欄位」，會由 build_school_context()
直接注入 prompt；這裡的知識條目則是給關鍵字檢索用的自然語言版本，
讓學生問「中大的國際處在哪」時也能從知識庫命中。

兩者共用 users/school_data.py 這份查核結果，不會有兩套互相矛盾的資料。
"""

from users.school_data import VERIFIED_SCHOOLS
from users.management.commands.seed_schools import SCHOOL_SEED, clean_label


def _build_school_entry(code, data):
    from users.models import StudentProfile

    labels = dict(StudentProfile.UNIVERSITY_CHOICES)
    name = clean_label(labels.get(code, code))
    aliases = SCHOOL_SEED.get(code, ('', ''))[1]

    lines = [f'【{name}的基本校務資訊】']

    if data.get('address'):
        lines.append(f'校本部地址：{data["address"]}')
    if data.get('main_tel'):
        lines.append(f'學校總機：{data["main_tel"]}')
    if data.get('website'):
        lines.append(f'官方網站：{data["website"]}')

    if data.get('intl_office_name'):
        office = f'{data["intl_office_name"]}：{data.get("intl_office_tel", "")}'
        if data.get('intl_office_ext'):
            office += f' 轉 {data["intl_office_ext"]}'
        lines.append(office.strip())
        if data.get('intl_office_url'):
            lines.append(f'國際處網站：{data["intl_office_url"]}')

    units = data.get('units', [])
    if units:
        lines.append('')
        lines.append('【校內單位位置與聯絡方式】')
        for unit in units:
            parts = [unit['name']]
            if unit.get('location'):
                parts.append(f'位置：{unit["location"]}')
            else:
                parts.append('位置：目前查無具體大樓位置，請洽總機或該處室分機確認')
            if unit.get('tel'):
                phone = unit['tel']
                if unit.get('ext'):
                    phone += f' 轉 {unit["ext"]}'
                parts.append(f'電話：{phone}')
            if unit.get('email'):
                parts.append(f'信箱：{unit["email"]}')
            if unit.get('office_hours'):
                parts.append(f'服務時間：{unit["office_hours"]}')
            lines.append('- ' + '，'.join(parts))

    lines.append('')
    lines.append(
        '以上資料若與學校最新公告不符，請以學校官網為準，'
        '並回報給我們更新。找不到的單位請撥打學校總機轉接。'
    )

    return {
        'category': 'school_info',
        'university': code,
        'title': f'{name}的地址、電話與校內單位',
        'keywords': f'{name}, {aliases}, 地址, 電話, 總機, 分機, 國際處, 校內單位, address, phone, campus',
        'content': '\n'.join(lines),
        'source_url': data.get('source', ''),
        'verified_at': data.get('verified'),
    }


ENTRIES = [_build_school_entry(code, data) for code, data in VERIFIED_SCHOOLS.items()]

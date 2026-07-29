"""
users/management/commands/seed_schools.py

建立 UNIVERSITY_CHOICES 中 36 所學校的 School 資料列，
只填「可從既有選項推導、且不需要查證數字」的欄位：全名、英文名、常見簡稱。

地址、總機、分機、行事曆網址一律留空，last_verified_at 也留空，
後台會顯示為「尚未查核」，由管理員或後續的抓取流程對照官網補齊。
本指令不會覆蓋已經填好的資料，可重複執行。

用法：
    python manage.py seed_schools
"""

from django.core.management.base import BaseCommand

from users.models import School

# code: (英文全名, 常見簡稱)
# 簡稱是學生實際會打出來的稱呼，chatbot 靠這個認出「中大」＝國立中央大學
SCHOOL_SEED = {
    'NTU':     ('National Taiwan University', '台大,臺大,NTU'),
    'NCCU':    ('National Chengchi University', '政大,政治大學,NCCU'),
    'NTHU':    ('National Tsing Hua University', '清大,清華,清華大學,NTHU'),
    'NYCU':    ('National Yang Ming Chiao Tung University', '陽明交大,陽交大,交大,陽明交通大學,NYCU'),
    'NCKU':    ('National Cheng Kung University', '成大,成功大學,NCKU'),
    'NCHU':    ('National Chung Hsing University', '興大,中興,中興大學,NCHU'),
    'NCU':     ('National Central University', '中央,中大,中央大學,NCU'),
    'NSYSU':   ('National Sun Yat-sen University', '中山,中山大學,NSYSU'),
    'NTNU':    ('National Taiwan Normal University', '師大,台師大,臺師大,NTNU'),
    'NTPU':    ('National Taipei University', '北大,台北大學,臺北大學,NTPU'),
    'NUTN':    ('National University of Tainan', '南大,台南大學,臺南大學,NUTN'),
    'NCYU':    ('National Chiayi University', '嘉大,嘉義大學,NCYU'),
    'NDHU':    ('National Dong Hwa University', '東華,東華大學,NDHU'),
    'NCNU':    ('National Chi Nan University', '暨大,暨南,暨南國際大學,NCNU'),
    'NIU':     ('National Ilan University', '宜大,宜蘭大學,NIU'),
    'NUU':     ('National United University', '聯大,聯合大學,NUU'),
    'NTTU':    ('National Taitung University', '東大,台東大學,臺東大學,NTTU'),
    'NQU':     ('National Quemoy University', '金大,金門大學,NQU'),
    'NPU':     ('National Penghu University of Science and Technology', '澎科大,澎湖科大,NPU'),
    'NTUST':   ('National Taiwan University of Science and Technology', '台科大,臺科大,台灣科大,NTUST'),
    'NTUT':    ('National Taipei University of Technology', '北科大,台北科大,臺北科大,NTUT'),
    'NKUST':   ('National Kaohsiung University of Science and Technology', '高科大,高雄科大,NKUST'),
    'YunTech': ('National Yunlin University of Science and Technology', '雲科大,雲林科大,YunTech'),
    'NPUST':   ('National Pingtung University of Science and Technology', '屏科大,屏東科大,NPUST'),
    'NTCUST':  ('National Taichung University of Science and Technology', '中科大,台中科大,臺中科大,NTCUST'),
    'NFU':     ('National Formosa University', '虎科大,虎尾科大,NFU'),
    'NKUHT':   ('National Kaohsiung University of Hospitality and Tourism', '高餐,高餐大,高雄餐旅,NKUHT'),
    'NKNU':    ('National Kaohsiung Normal University', '高師大,高雄師大,NKNU'),
    'NCUE':    ('National Changhua University of Education', '彰師大,彰化師大,NCUE'),
    'NTUE':    ('National Taipei University of Education', '北教大,國北教大,台北教育大學,NTUE'),
    'NTCU':    ('National Taichung University of Education', '中教大,台中教育大學,臺中教育大學,NTCU'),
    'NPTU':    ('National Pingtung University', '屏大,屏東大學,NPTU'),
    'NTUS':    ('National Taiwan University of Sport', '台體大,臺體大,臺灣體大,NTUS'),
    'NTUB':    ('National Taipei University of Business', '北商大,台北商大,臺北商業大學,NTUB'),
    'NOU':     ('National Open University', '空大,空中大學,NOU'),
}


def clean_label(label):
    """'國立臺灣大學（NTU）' → '國立臺灣大學'"""
    return str(label).split('（')[0].strip()


class Command(BaseCommand):
    help = '建立 36 所學校的 School 基本資料（全名 / 英文名 / 簡稱），不覆蓋既有內容'

    def handle(self, *args, **options):
        from users.models import StudentProfile

        labels = dict(StudentProfile.UNIVERSITY_CHOICES)
        created_count = 0
        filled_count = 0

        for code, (name_en, aliases) in SCHOOL_SEED.items():
            label = labels.get(code)
            if not label:
                self.stderr.write(f'跳過 {code}：UNIVERSITY_CHOICES 中沒有這個代碼')
                continue

            name = clean_label(label)
            school, created = School.objects.get_or_create(
                code=code,
                defaults={'name': name, 'name_en': name_en, 'aliases': aliases},
            )

            if created:
                created_count += 1
                continue

            # 已存在：只補空欄位，不動管理員已經填好或查核過的內容
            updates = []
            if not school.name:
                school.name = name
                updates.append('name')
            if not school.name_en:
                school.name_en = name_en
                updates.append('name_en')
            if not school.aliases:
                school.aliases = aliases
                updates.append('aliases')
            if updates:
                school.save(update_fields=updates)
                filled_count += 1

        verified_count, unit_count = self._apply_verified_data()

        if options['verbosity']:
            total = School.objects.count()
            pending = total - verified_count
            self.stdout.write(self.style.SUCCESS(
                f'完成：新增 {created_count} 所、補齊 {filled_count} 所，目前共 {total} 筆學校資料。'
            ))
            self.stdout.write(
                f'已查核並寫入詳細校務資料：{verified_count} 所（含 {unit_count} 個校內單位）。'
            )
            self.stdout.write(self.style.WARNING(
                f'尚有 {pending} 所只有校名與簡稱，地址、總機、分機皆為空白且未查核。'
                '請到後台「學校資料」對照官網補齊，或擴充 users/school_data.py。'
            ))

    def _apply_verified_data(self):
        """
        把 users/school_data.py 中已查核的校務資料寫入 School / SchoolUnit。
        只覆蓋資料檔有提供的欄位，資料檔沒寫的欄位保持原狀（可能是管理員手動填的）。
        """
        from users.models import School, SchoolUnit
        from users.school_data import VERIFIED_SCHOOLS

        verified_count = unit_count = 0

        for code, data in VERIFIED_SCHOOLS.items():
            school = School.objects.filter(code=code).first()
            if not school:
                continue

            units = data.get('units', [])
            fields = {
                k: v for k, v in data.items()
                if k not in ('units', 'source', 'verified')
            }
            fields['last_verified_at'] = data['verified']

            for field, value in fields.items():
                setattr(school, field, value)
            school.save(update_fields=list(fields))
            verified_count += 1

            for order, unit in enumerate(units):
                SchoolUnit.objects.update_or_create(
                    school=school, name=unit['name'],
                    defaults={**{k: v for k, v in unit.items() if k != 'name'},
                              'order': order, 'is_active': True},
                )
                unit_count += 1

        return verified_count, unit_count

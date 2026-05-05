"""
python manage.py seed_flow_templates

預置來臺就學的任務模板。
- 安全可重複執行（依 title+category 做 get_or_create）
- 加 --clear 旗標可清空後重建
"""

from django.core.management.base import BaseCommand
from flow.models import FlowStepTemplate


TEMPLATES = [
    # ── 申請階段（applied）────────────────────────────────────────
    {
        'title':        '確認申請文件完整性',
        'description':  '核查入學申請所需文件（成績單、推薦信、護照等）是否齊全。',
        'category':     'enrollment',
        'admission_statuses': ['applied'],
        'order':        10,
        'is_required':  True,
    },
    {
        'title':        '準備財力證明',
        'description':  '備妥銀行存款證明或擔保人財力文件，供簽證審查使用。',
        'category':     'finance',
        'admission_statuses': ['applied', 'admitted'],
        'order':        11,
        'is_required':  True,
    },
    {
        'title':        '了解學校宿舍申請程序',
        'description':  '查詢目標學校宿舍申請期限、費用及備選住宿方案。',
        'category':     'housing',
        'admission_statuses': ['applied', 'admitted'],
        'order':        12,
    },

    # ── 錄取後（admitted）────────────────────────────────────────
    {
        'title':        '確認錄取通知書',
        'description':  '確認錄取通知書（Admission Letter）的內容：入學日期、就讀系所、必要手續。',
        'category':     'enrollment',
        'admission_statuses': ['admitted', 'pre_arrival'],
        'order':        20,
        'is_required':  True,
    },
    {
        'title':        '申請學生簽證（居留簽）',
        'description':  '持錄取通知書至台灣駐外辦事處申請學生居留簽證（停留簽或居留簽）。',
        'category':     'visa',
        'identity_types': ['foreign_student', 'overseas_chinese'],
        'admission_statuses': ['admitted', 'pre_arrival'],
        'order':        21,
        'is_required':  True,
        'days_offset':  -60,
    },
    {
        'title':        '申請入學許可函（僑委會）',
        'description':  '僑生須向僑務委員會申請入學許可函，作為辦理居留的依據。',
        'category':     'visa',
        'identity_types': ['overseas_chinese', 'preparatory'],
        'admission_statuses': ['admitted', 'pre_arrival'],
        'order':        22,
        'is_required':  True,
        'days_offset':  -90,
    },
    {
        'title':        '訂機票並確認入學日期',
        'description':  '提早訂購機票，確保在學校報到日前抵臺。',
        'category':     'other',
        'admission_statuses': ['admitted', 'pre_arrival'],
        'order':        23,
        'days_offset':  -30,
    },
    {
        'title':        '申請學校宿舍或確認住宿',
        'description':  '向學校申請宿舍，或聯繫校外房東確認租約與入住日期。',
        'category':     'housing',
        'admission_statuses': ['admitted', 'pre_arrival'],
        'order':        24,
        'is_required':  True,
        'days_offset':  -30,
    },

    # ── 抵台前（pre_arrival）──────────────────────────────────────
    {
        'title':        '辦理出國健康檢查',
        'description':  '前往認可醫院完成胸部 X 光及傳染病篩檢，部分學校要求入學前提交。',
        'category':     'health',
        'admission_statuses': ['pre_arrival'],
        'order':        30,
        'is_required':  True,
        'days_offset':  -14,
    },
    {
        'title':        '準備臺幣現金或換匯',
        'description':  '備妥抵台初期生活費（建議約 NTD 30,000），並了解換匯管道。',
        'category':     'finance',
        'admission_statuses': ['pre_arrival'],
        'order':        31,
    },
    {
        'title':        '了解台灣生活資訊',
        'description':  '閱讀台灣生活指南：交通、飲食、氣候、文化等基本知識。',
        'category':     'culture',
        'admission_statuses': ['pre_arrival'],
        'order':        32,
    },
    {
        'title':        '確認接機安排',
        'description':  '聯繫學校迎新服務或安排親友接機，確認抵達台灣後的交通。',
        'category':     'other',
        'admission_statuses': ['pre_arrival'],
        'order':        33,
        'days_offset':  -7,
    },

    # ── 已抵台（arrived）──────────────────────────────────────────
    {
        'title':        '學校報到並完成入學手續',
        'description':  '攜帶所有文件至學校國際事務處完成正式報到及選課手續。',
        'category':     'enrollment',
        'admission_statuses': ['arrived'],
        'order':        40,
        'is_required':  True,
        'days_offset':  3,
    },
    {
        'title':        '申辦居留證（ARC）',
        'description':  '持簽證、護照、照片及在學證明至內政部移民署轄區服務站申辦外僑居留證。',
        'category':     'visa',
        'identity_types': ['foreign_student'],
        'admission_statuses': ['arrived'],
        'order':        41,
        'is_required':  True,
        'days_offset':  14,
    },
    {
        'title':        '辦理加入全民健保',
        'description':  '抵台滿 6 個月後自動納保，或由學校統一加保；確認健保卡申請流程。',
        'category':     'health',
        'admission_statuses': ['arrived'],
        'order':        42,
        'is_required':  True,
        'days_offset':  30,
    },
    {
        'title':        '開設臺灣銀行帳戶',
        'description':  '持護照、居留證及在學證明至銀行（建議郵局或台灣銀行）開立帳戶。',
        'category':     'finance',
        'admission_statuses': ['arrived'],
        'order':        43,
        'days_offset':  21,
    },
    {
        'title':        '辦理台灣手機門號',
        'description':  '持護照或居留證至電信門市（中華、台哥大、遠傳等）辦理預付卡或月租門號。',
        'category':     'other',
        'admission_statuses': ['arrived'],
        'order':        44,
        'days_offset':  7,
    },
    {
        'title':        '熟悉校園環境與資源',
        'description':  '參加學校迎新活動，了解圖書館、學生輔導、醫療中心等校內資源。',
        'category':     'culture',
        'admission_statuses': ['arrived'],
        'order':        45,
    },
    {
        'title':        '報名華語或中文課程',
        'description':  '查詢學校語言中心或外部華語中心，報名適合自己程度的課程。',
        'category':     'language',
        'admission_statuses': ['arrived'],
        'order':        46,
    },

    # ── 所有階段通用 ─────────────────────────────────────────────
    {
        'title':        '加入學校國際生社群',
        'description':  '透過 Facebook、Line 等加入學校國際學生群組，認識同學並取得最新資訊。',
        'category':     'culture',
        'order':        50,
        'is_required':  False,
    },
]


class Command(BaseCommand):
    help = '預置來臺就學任務模板到資料庫'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='先清空所有模板再重新建立')

    def handle(self, *args, **options):
        if options['clear']:
            count = FlowStepTemplate.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'已刪除 {count} 筆模板'))

        created = updated = 0
        for t in TEMPLATES:
            obj, is_new = FlowStepTemplate.objects.update_or_create(
                title    = t['title'],
                category = t['category'],
                defaults = {
                    'description':        t.get('description', ''),
                    'identity_types':     t.get('identity_types', []),
                    'admission_statuses': t.get('admission_statuses', []),
                    'order':              t.get('order', 0),
                    'is_required':        t.get('is_required', True),
                    'days_offset':        t.get('days_offset', None),
                    'reference_url':      t.get('reference_url', ''),
                    'is_active':          True,
                },
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'完成！新增 {created} 筆，更新 {updated} 筆任務模板。'
        ))

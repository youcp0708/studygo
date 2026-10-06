"""
python manage.py seed_insights_demo [--students 1300] [--seed 42] [--clear]

產生「模擬」分析資料（is_demo=True），用於 Demo 與 Power BI 開發。
- 只寫入 insights_* 分析表，不碰 StudentProfile / StudentTask 等營運資料。
- Dashboard 預設不顯示模擬資料；要顯示請在 .env 設定 INSIGHTS_USE_DEMO_DATA=True，
  畫面上會出現「示範資料」標示。
- 刻意埋入一個可被預警抓到的情境：115 學年度外籍生的居留證件逾期率上升。
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from insights.alerts import rebuild_alerts
from insights.metrics import academic_year_of, arrival_cohort_of
from insights.models import DimStudent, FactQuestion, FactStudentTask, InsightAlert

UNIVERSITIES = [('NCU', 0.4), ('NTU', 0.25), ('NCCU', 0.2), ('NCKU', 0.15)]
IDENTITIES = [('overseas_chinese', 0.48), ('foreign_student', 0.40), ('hong_kong_macau', 0.12)]
NATIONALITIES = {
    'overseas_chinese': [('Malaysia', 0.55), ('Indonesia', 0.2), ('Myanmar', 0.15), ('Thailand', 0.05), ('Vietnam', 0.05)],
    'foreign_student': [('Vietnam', 0.25), ('Indonesia', 0.2), ('Japan', 0.12), ('Korea', 0.12), ('Thailand', 0.1),
                        ('India', 0.08), ('USA', 0.05), ('France', 0.04), ('Philippines', 0.04)],
    'hong_kong_macau': [('Hong Kong', 0.75), ('Macau', 0.25)],
}
REGIONS = {
    'Malaysia': 'Southeast Asia', 'Indonesia': 'Southeast Asia', 'Myanmar': 'Southeast Asia',
    'Thailand': 'Southeast Asia', 'Vietnam': 'Southeast Asia', 'Philippines': 'Southeast Asia',
    'Japan': 'East Asia', 'Korea': 'East Asia', 'Hong Kong': 'East Asia', 'Macau': 'East Asia',
    'India': 'South Asia', 'USA': 'North America', 'France': 'Europe',
}
LANGUAGES = {
    'Malaysia': 'ms', 'Indonesia': 'id', 'Myanmar': 'my', 'Thailand': 'th', 'Vietnam': 'vi',
    'Japan': 'ja', 'Korea': 'ko', 'Hong Kong': 'zh-hant', 'Macau': 'zh-hant',
}
# 抵台月份（年, 月）與權重
COHORTS = [((2025, 2), 0.15), ((2025, 9), 0.35), ((2026, 2), 0.15), ((2026, 9), 0.35)]

# 任務分類 → (相對抵台日的截止天數, 基礎逾期機率)
TASKS = {
    'entry_permit': (-30, 0.04),
    'residence_permit': (15, 0.08),
    'nhi': (190, 0.12),
    'housing': (-14, 0.05),
    'registration': (3, 0.15),
    'health_check': (30, 0.10),
    'course': (10, 0.07),
}
QUESTION_WEIGHTS = {
    'residence_permit': 0.24, 'entry_permit': 0.16, 'housing': 0.14, 'nhi': 0.10, 'registration': 0.08,
    'course': 0.07, 'health_check': 0.05, 'bank': 0.05, 'work_permit': 0.04, 'scholarship': 0.03,
    'medical': 0.02, 'daily_life': 0.01, 'other': 0.01,
}


def pick(rng, weighted):
    values, weights = zip(*weighted)
    return rng.choices(values, weights=weights)[0]


class Command(BaseCommand):
    help = 'Student Insights：產生模擬分析資料（is_demo=True）'

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=1300)
        parser.add_argument('--seed', type=int, default=42)
        parser.add_argument('--clear', action='store_true', help='只刪除模擬資料，不重新產生')

    @transaction.atomic
    def handle(self, *args, **options):
        for model in (DimStudent, FactStudentTask, FactQuestion, InsightAlert):
            model.objects.filter(is_demo=True).delete()
        if options['clear']:
            self.stdout.write(self.style.SUCCESS('已刪除所有模擬資料'))
            return

        rng = random.Random(options['seed'])
        today = timezone.localdate()
        dims, facts, questions = [], [], []

        for i in range(options['students']):
            identity = pick(rng, IDENTITIES)
            nationality = pick(rng, NATIONALITIES[identity])
            if rng.random() < 0.03:
                arrival = None
            else:
                (y, m) = pick(rng, COHORTS)
                arrival = date(y, m, rng.randint(1, 25))
            dim = {
                'snapshot_date': today,
                'is_demo': True,
                'student_key': f'demo{i:06d}',
                'university': pick(rng, UNIVERSITIES),
                'nationality': nationality,
                'region': REGIONS.get(nationality, ''),
                'identity_type': identity,
                'arrival_cohort': arrival_cohort_of(arrival),
                'academic_year': academic_year_of(arrival),
            }
            dims.append(DimStudent(
                admission_status='arrived' if arrival and arrival <= today else 'pre_arrival',
                preferred_language=LANGUAGES.get(nationality, 'en'),
                **dim,
            ))

            for category, (offset, base_p) in TASKS.items():
                if identity == 'hong_kong_macau' and category == 'entry_permit':
                    base_p = 0.02
                facts.append(self._fact(rng, dim, category, arrival, offset, base_p, identity, nationality, today))
            # 一個沒有截止日的任務（例如銀行開戶）
            facts.append(self._fact(rng, dim, 'other', None, None, 0, identity, nationality, today))

            for _ in range(rng.choices([0, 1, 2, 3, 4, 5, 6], weights=[2, 3, 3, 2, 1, 1, 1])[0]):
                weights = dict(QUESTION_WEIGHTS)
                if identity == 'foreign_student':
                    weights['residence_permit'] += 0.10
                if nationality in ('Vietnam', 'Indonesia'):
                    weights['residence_permit'] += 0.06
                category = rng.choices(list(weights), weights=list(weights.values()))[0]
                asked = today - timedelta(days=rng.randint(0, 400))
                questions.append(FactQuestion(category=category, asked_date=asked, **dim))

        DimStudent.objects.bulk_create(dims, batch_size=1000)
        FactStudentTask.objects.bulk_create(facts, batch_size=1000)
        FactQuestion.objects.bulk_create(questions, batch_size=1000)
        alerts = rebuild_alerts(today, is_demo=True)

        self.stdout.write(self.style.SUCCESS(
            f'已產生模擬資料：學生 {len(dims)}、學生任務 {len(facts)}、提問 {len(questions)}、預警 {alerts}'
        ))
        self.stdout.write('要在 Dashboard 顯示模擬資料，請在 .env 設定 INSIGHTS_USE_DEMO_DATA=True')

    def _fact(self, rng, dim, category, arrival, offset, base_p, identity, nationality, today):
        due = arrival + timedelta(days=offset) if arrival and offset is not None else None
        has_deadline = due is not None
        is_due = has_deadline and due < today

        p_overdue = base_p
        # 埋入的情境：115 學年度外籍生居留證件逾期率上升，越南、印尼籍更明顯
        if category == 'residence_permit' and dim['academic_year'] == 115 and identity == 'foreign_student':
            p_overdue += 0.12
            if nationality in ('Vietnam', 'Indonesia'):
                p_overdue += 0.05
        reminded = has_deadline and rng.random() < 0.6
        if reminded:
            p_overdue *= 0.6

        overdue_open = overdue_late = False
        completed_date = None
        if is_due:
            if rng.random() < p_overdue:
                if rng.random() < 0.5:
                    # is_due 代表 due < today，所以完成日一定晚於截止日
                    overdue_late = True
                    completed_date = min(due + timedelta(days=rng.randint(1, 20)), today)
                else:
                    overdue_open = True
            else:
                completed_date = due - timedelta(days=rng.randint(0, 10))
        elif not has_deadline:
            if rng.random() < 0.7:
                completed_date = today - timedelta(days=rng.randint(0, 200))
        elif rng.random() < 0.3:
            completed_date = today - timedelta(days=rng.randint(0, 5))

        is_completed = completed_date is not None
        if is_completed:
            status = 'completed'
        else:
            status = rng.choice(['not_started', 'in_progress'])

        return FactStudentTask(
            task_category=category,
            is_required=True,
            has_deadline=has_deadline,
            due_date=due,
            status=status,
            completed_date=completed_date,
            is_completed=is_completed,
            is_due=is_due,
            is_overdue_open=overdue_open,
            is_overdue_late=overdue_late,
            is_overdue=overdue_open or overdue_late,
            is_possibly_unreported=overdue_open and rng.random() < 0.25,
            reminder_count=1 if reminded else 0,
            **dim,
        )

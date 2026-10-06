"""
insights/services.py
給 views 使用的查詢：依權限範圍與篩選條件取出分析表的 queryset。
指標計算本身在 metrics.py，這裡不重算。
"""

import re

from django.db.models import Count, Max

from users.models import StudentProfile

from . import conf
from .metrics import label_for
from .models import DimStudent, FactQuestion, FactStudentTask, InsightAlert
from .permissions import ALL_SCHOOLS

_IDENTITY_CODES = {code for code, _ in StudentProfile.IDENTITY_CHOICES}
_NATIONALITY_CODES = {code for code, _ in StudentProfile.NATIONALITY_CHOICES}
_UNIVERSITY_CODES = {code for code, _ in StudentProfile.UNIVERSITY_CHOICES}
_COHORT_RE = re.compile(r'^\d{4}-\d{2}$')


def parse_filters(params, scope):
    """驗證網址參數；不合法的值直接忽略。校方人員不能用 school 參數看別校。"""
    filters = {}
    if params.get('identity_type') in _IDENTITY_CODES:
        filters['identity_type'] = params['identity_type']
    if params.get('nationality') in _NATIONALITY_CODES:
        filters['nationality'] = params['nationality']
    if _COHORT_RE.match(params.get('arrival_cohort', '')):
        filters['arrival_cohort'] = params['arrival_cohort']
    if scope == ALL_SCHOOLS and params.get('school') in _UNIVERSITY_CODES:
        filters['school'] = params['school']
    return filters


def datasets(scope, filters):
    """
    回傳 {'dim', 'fact', 'questions', 'alerts', 'school'}。
    alerts 不套用族群篩選（預警本身就是以族群分析產生的）。
    """
    demo = conf.use_demo_data()
    dim = DimStudent.objects.filter(is_demo=demo)
    fact = FactStudentTask.objects.filter(is_demo=demo)
    questions = FactQuestion.objects.filter(is_demo=demo)
    alerts = InsightAlert.objects.filter(is_demo=demo)

    school = scope if scope != ALL_SCHOOLS else filters.get('school')
    if school:
        dim, fact, questions = (qs.filter(university=school) for qs in (dim, fact, questions))
        alerts = alerts.filter(university=school)
    else:
        alerts = alerts.filter(university=ALL_SCHOOLS)

    group_filters = {k: v for k, v in filters.items() if k != 'school'}
    if group_filters:
        dim, fact, questions = (qs.filter(**group_filters) for qs in (dim, fact, questions))

    return {'dim': dim, 'fact': fact, 'questions': questions, 'alerts': alerts, 'school': school}


def snapshot_date():
    return DimStudent.objects.filter(is_demo=conf.use_demo_data()).aggregate(d=Max('snapshot_date'))['d']


def filter_options(scope, filters):
    """篩選下拉選單。只列出人數 ≥ MIN_DISPLAY_N 的國籍與梯次，避免透露小族群的存在。"""
    base = datasets(scope, {'school': filters['school']} if 'school' in filters else {})['dim']

    def options(field):
        rows = base.values(field).annotate(c=Count('id')).filter(c__gte=conf.MIN_DISPLAY_N).order_by(field)
        return [(r[field], label_for(field, r[field])) for r in rows if r[field]]

    return {
        'identity_type': [(code, str(label)) for code, label in StudentProfile.IDENTITY_CHOICES],
        'nationality': options('nationality'),
        'arrival_cohort': options('arrival_cohort'),
        'school': (
            [(code, str(label)) for code, label in StudentProfile.UNIVERSITY_CHOICES]
            if scope == ALL_SCHOOLS else []
        ),
    }

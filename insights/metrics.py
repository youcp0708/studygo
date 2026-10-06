"""
insights/metrics.py
所有指標的唯一計算來源（定義見規格 §7）。

- 輸入一律是分析表（FactStudentTask / FactQuestion / DimStudent）的 queryset，
  不直接讀 StudentProfile、StudentTask 等營運資料表。
- 比率一律以 make_rate() 包裝：同時帶 n，n 太小時 suppressed=True、不給數字。
"""

from datetime import date

from django.db.models import Count, Q

from users.models import StudentProfile

from . import conf
from .question_categories import QUESTION_CATEGORY_LABELS
from .task_categories import TASK_CATEGORY_CHOICES, TASK_CATEGORY_LABELS

DIMENSION_LABELS = {
    'identity_type': '身份別',
    'nationality': '國籍',
    'arrival_cohort': '抵台梯次',
    'university': '學校',
    'admission_status': '入學狀態',
}

_CHOICE_LABELS = {
    'identity_type': dict(StudentProfile.IDENTITY_CHOICES),
    'nationality': dict(StudentProfile.NATIONALITY_CHOICES),
    'university': dict(StudentProfile.UNIVERSITY_CHOICES),
    'admission_status': dict(StudentProfile.ADMISSION_STATUS_CHOICES),
    'task_category': TASK_CATEGORY_LABELS,
    'category': QUESTION_CATEGORY_LABELS,
}


def label_for(dimension, value):
    """把代碼轉成顯示名稱，例如 identity_type/foreign_student → 外籍生。"""
    if dimension == 'arrival_cohort':
        return f'{value} 梯次' if value else '未填抵台日'
    if dimension == 'academic_year':
        return f'{value} 學年度' if value else '未填抵台日'
    label = _CHOICE_LABELS.get(dimension, {}).get(value)
    return str(label) if label else (value or '未填')


# ══════════════════════════════════════════
# 年度
# ══════════════════════════════════════════
def academic_year_of(d):
    """學年度（民國年）：8/1 起算。2026-09-01 → 115；2026-03-01 → 114。"""
    if d is None:
        return None
    return d.year - 1911 if d.month >= 8 else d.year - 1912


def arrival_cohort_of(d):
    return d.strftime('%Y-%m') if d else ''


def current_academic_year(today=None):
    return academic_year_of(today or date.today())


# ══════════════════════════════════════════
# 比率
# ══════════════════════════════════════════
def make_rate(count, n, min_n=None):
    """回傳 {'rate': 百分比(一位小數) 或 None, 'n', 'count', 'suppressed'}。"""
    min_n = conf.MIN_DISPLAY_N if min_n is None else min_n
    if n < min_n or n == 0:
        return {'rate': None, 'n': n, 'count': count, 'suppressed': True}
    return {'rate': round(count * 100.0 / n, 1), 'n': n, 'count': count, 'suppressed': False}


# ══════════════════════════════════════════
# 任務指標（§7.2、§7.3）
# ══════════════════════════════════════════
def required_tasks(fact_qs):
    """完成率／逾期率只計算必做任務。"""
    return fact_qs.filter(is_required=True)


_TASK_AGGREGATES = {
    'assigned': Count('id'),
    'due_n': Count('id', filter=Q(is_due=True)),
    'due_completed': Count('id', filter=Q(is_due=True, is_completed=True)),
    'overdue': Count('id', filter=Q(is_overdue=True)),
    'overdue_open': Count('id', filter=Q(is_overdue_open=True)),
    'unreported': Count('id', filter=Q(is_possibly_unreported=True)),
    'nodeadline_n': Count('id', filter=Q(has_deadline=False)),
    'nodeadline_completed': Count('id', filter=Q(has_deadline=False, is_completed=True)),
    'overdue_students': Count('student_key', filter=Q(is_overdue=True), distinct=True),
}


def _task_row(agg):
    return {
        'assigned': agg['assigned'],
        # 完成率：已完成 ÷ 已到期（截止日已過）
        'completion': make_rate(agg['due_completed'], agg['due_n']),
        # 逾期率：逾期（未完成 + 逾期完成）÷ 已到期
        'overdue': make_rate(agg['overdue'], agg['due_n']),
        # 可能未回報：逾期未完成之中，30 天沒登入的比例
        'unreported': make_rate(agg['unreported'], agg['overdue_open']),
        # 無期限任務：已完成 ÷ 全部指派
        'nodeadline_completion': make_rate(agg['nodeadline_completed'], agg['nodeadline_n']),
        'overdue_count': agg['overdue'],
        'overdue_students': agg['overdue_students'],
    }


def task_summary(fact_qs):
    """整體任務指標（單一列）。"""
    return _task_row(required_tasks(fact_qs).aggregate(**_TASK_AGGREGATES))


def task_metrics_by(fact_qs, field):
    """依某個欄位分組的任務指標，例如 field='task_category'。"""
    rows = (
        required_tasks(fact_qs)
        .values(field)
        .annotate(**_TASK_AGGREGATES)
        .order_by(field)
    )
    result = []
    for agg in rows:
        value = agg[field]
        row = _task_row(agg)
        row.update({'value': value, 'label': label_for(field, value)})
        result.append(row)
    if field == 'task_category':
        order = [code for code, _ in TASK_CATEGORY_CHOICES]
        result.sort(key=lambda r: order.index(r['value']) if r['value'] in order else len(order))
    return result


def overdue_trend_by_cohort(fact_qs, task_category=None):
    """依抵台梯次的逾期率趨勢（不含未填抵台日的學生）。"""
    qs = fact_qs.exclude(arrival_cohort='')
    if task_category:
        qs = qs.filter(task_category=task_category)
    return task_metrics_by(qs, 'arrival_cohort')


def task_metrics_grouped(fact_qs, fields):
    """依多個欄位交叉分組的任務指標（CSV 匯出用）。每列帶 values / labels 兩個 dict。"""
    rows = required_tasks(fact_qs).values(*fields).annotate(**_TASK_AGGREGATES).order_by(*fields)
    result = []
    for agg in rows:
        row = _task_row(agg)
        row['values'] = {f: agg[f] for f in fields}
        row['labels'] = {f: label_for(f, agg[f]) for f in fields}
        result.append(row)
    return result


def compare_periods(fact_qs, task_category=None):
    """
    各任務分類「最近兩個期間」的逾期率比較（規格 §12.2 第 4 題）。
    期間優先用學年度；某分類的學年度不足兩個（分母 ≥ MIN_DISPLAY_N）時，改用抵台梯次。
    回傳依 delta_pp 由小到大排序（改善最多的在前）；無法比較的分類 delta_pp 為 None、排最後。
    """
    qs = required_tasks(fact_qs).filter(is_due=True)
    codes = [task_category] if task_category else [c for c, _ in TASK_CATEGORY_CHOICES if c != 'other']

    result = []
    for code in codes:
        cat_qs = qs.filter(task_category=code)
        row = {'value': code, 'label': label_for('task_category', code), 'period_type': None,
               'current_label': None, 'current': None, 'baseline_label': None, 'baseline': None, 'delta_pp': None}
        for field in ('academic_year', 'arrival_cohort'):
            # 排除未填抵台日的學生（academic_year 為 NULL、arrival_cohort 為空字串）
            missing = {'academic_year__isnull': True} if field == 'academic_year' else {'arrival_cohort': ''}
            stats = cat_qs.exclude(**missing)
            periods = [
                (r[field], r['od'], r['n'])
                for r in stats.values(field).annotate(n=Count('id'), od=Count('id', filter=Q(is_overdue=True)))
                .order_by(field)
                if r['n'] >= conf.MIN_DISPLAY_N
            ]
            if len(periods) >= 2:
                (base_v, base_od, base_n), (cur_v, cur_od, cur_n) = periods[-2], periods[-1]
                current, baseline = make_rate(cur_od, cur_n), make_rate(base_od, base_n)
                row.update({
                    'period_type': field,
                    'current_label': label_for(field, cur_v),
                    'current': current,
                    'baseline_label': label_for(field, base_v),
                    'baseline': baseline,
                    'delta_pp': round(current['rate'] - baseline['rate'], 1),
                })
                break
        result.append(row)
    result.sort(key=lambda r: (r['delta_pp'] is None, r['delta_pp'] if r['delta_pp'] is not None else 0))
    return result


# ══════════════════════════════════════════
# 學生分布（Overview）
# ══════════════════════════════════════════
def distribution(dim_qs, field, top=None):
    """
    人數分布。人數 < MIN_DISPLAY_N 的組別併入「其他（樣本不足）」，避免小族群被識別。
    top：只列前幾名，其餘併入「其他」。
    """
    total = dim_qs.count()
    rows = list(dim_qs.values(field).annotate(count=Count('id')).order_by('-count', field))
    shown, other = [], 0
    for r in rows:
        if r['count'] < conf.MIN_DISPLAY_N or (top and len(shown) >= top):
            other += r['count']
        else:
            shown.append({
                'value': r[field],
                'label': label_for(field, r[field]),
                'count': r['count'],
                'pct': round(r['count'] * 100.0 / total, 1) if total else 0,
            })
    if other:
        shown.append({
            'value': '_other',
            'label': '其他（含樣本不足組別）',
            'count': other,
            'pct': round(other * 100.0 / total, 1) if total else 0,
        })
    return shown


def student_overview(dim_qs, today=None):
    ay = current_academic_year(today)
    return {
        'total': dim_qs.count(),
        'academic_year': ay,
        'new_students': dim_qs.filter(academic_year=ay).count(),
        'missing_arrival': dim_qs.filter(arrival_cohort='').count(),
        'by_identity': distribution(dim_qs, 'identity_type'),
        'by_nationality': distribution(dim_qs, 'nationality', top=6),
        'by_admission_status': distribution(dim_qs, 'admission_status'),
        'by_university': distribution(dim_qs, 'university', top=10),
    }


# ══════════════════════════════════════════
# 學生提問（§7.5）
# ══════════════════════════════════════════
def question_share(question_qs):
    """提問占比：某分類 ÷ 全部已分類提問。"""
    total = question_qs.count()
    rows = question_qs.values('category').annotate(count=Count('id')).order_by('-count')
    return {
        'total': total,
        'rows': [
            {
                'value': r['category'],
                'label': label_for('category', r['category']),
                'count': r['count'],
                'pct': round(r['count'] * 100.0 / total, 1) if total else 0,
            }
            for r in rows
        ],
    }


def question_rate_by(question_qs, dim_qs, field, category=None):
    """
    提問率：某族群的提問數 ÷ 該族群學生數 × 100（每 100 名學生的提問數）。
    跨國籍、跨身份比較只用這個指標，不用次數。
    """
    if category:
        question_qs = question_qs.filter(category=category)
    q_counts = dict(question_qs.values_list(field).annotate(c=Count('id')))
    result = []
    for value, students in dim_qs.values_list(field).annotate(c=Count('id')).order_by(field):
        questions = q_counts.get(value, 0)
        suppressed = students < conf.MIN_DISPLAY_N
        result.append({
            'value': value,
            'label': label_for(field, value),
            'students': students,
            'questions': questions,
            'per_100': None if suppressed else round(questions * 100.0 / students, 1),
            'suppressed': suppressed,
        })
    result.sort(key=lambda r: (r['per_100'] is None, -(r['per_100'] or 0)))
    return result


def question_rates_grouped(question_qs, dim_qs, fields):
    """
    提問分類 × 多個族群欄位的提問率（CSV 匯出用）。
    只列出有提問的組合；學生數 < MIN_DISPLAY_N 時 per_100 為 None。
    """
    students = {tuple(r[f] for f in fields): r['c']
                for r in dim_qs.values(*fields).annotate(c=Count('id'))}
    rows = question_qs.values('category', *fields).annotate(c=Count('id')).order_by('category', *fields)
    result = []
    for r in rows:
        group = tuple(r[f] for f in fields)
        n = students.get(group, 0)
        suppressed = n < conf.MIN_DISPLAY_N
        result.append({
            'category': r['category'],
            'category_label': label_for('category', r['category']),
            'labels': {f: label_for(f, r[f]) for f in fields},
            'students': n,
            'questions': r['c'],
            'per_100': None if suppressed else round(r['c'] * 100.0 / n, 1),
            'suppressed': suppressed,
        })
    return result


def needs_vs_overdue(question_qs, dim_qs, fact_qs):
    """
    任務分類層級的交叉分析：每 100 名學生的提問數 × 逾期率。
    兩者都高於平均的分類，代表流程說明最需要改善。
    """
    students = dim_qs.count()
    q_counts = dict(question_qs.values_list('category').annotate(c=Count('id')))
    overdue = {r['value']: r['overdue'] for r in task_metrics_by(fact_qs, 'task_category')}

    rows = []
    for code, label in TASK_CATEGORY_CHOICES:
        if code == 'other':
            continue
        per_100 = round(q_counts.get(code, 0) * 100.0 / students, 1) if students >= conf.MIN_DISPLAY_N else None
        rows.append({
            'value': code,
            'label': label,
            'questions_per_100': per_100,
            'overdue': overdue.get(code, make_rate(0, 0)),
        })

    q_values = [r['questions_per_100'] for r in rows if r['questions_per_100'] is not None]
    o_values = [r['overdue']['rate'] for r in rows if r['overdue']['rate'] is not None]
    q_avg = sum(q_values) / len(q_values) if q_values else None
    o_avg = sum(o_values) / len(o_values) if o_values else None
    for r in rows:
        r['needs_attention'] = bool(
            q_avg is not None and o_avg is not None
            and r['questions_per_100'] is not None and r['overdue']['rate'] is not None
            and r['questions_per_100'] > q_avg and r['overdue']['rate'] > o_avg
        )
    return {'rows': rows, 'questions_avg': q_avg, 'overdue_avg': o_avg}

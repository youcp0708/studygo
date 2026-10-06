"""
insights/alerts.py
風險預警規則（規格 §9）。

觸發條件（同時成立）：
1. 目前與基準的分母都 ≥ ALERT_MIN_N
2. 逾期率上升 ≥ ALERT_MIN_DELTA_PP 個百分點
3. 相對變化 ≥ ALERT_MIN_RELATIVE

比較基準依資料量自動選擇：前一學年度 → 上一個抵台梯次 → 整體平均（找偏高族群）。
行動建議只用固定範本產生，每一句都對應到資料結論，不產生資料中沒有依據的做法。
"""

from django.db.models import Count, Q

from . import conf
from .metrics import DIMENSION_LABELS, label_for, make_rate
from .models import FactStudentTask, InsightAlert
from .permissions import ALL_SCHOOLS
from .task_categories import TASK_CATEGORY_CHOICES

# 找集中族群時使用的維度
CONCENTRATION_DIMENSIONS = ['identity_type', 'nationality', 'arrival_cohort']
# 單一時間點時，用來找「偏高族群」的維度
GROUP_DIMENSIONS = ['identity_type', 'nationality']


def _group_label(dim, value):
    """族群名稱，國籍加上「籍」：越南 → 越南籍。"""
    label = label_for(dim, value)
    return f'{label}籍' if dim == 'nationality' else label


def _overdue_stats(qs, field):
    """依 field 分組，回傳 {value: (overdue, n)}。"""
    rows = qs.values(field).annotate(n=Count('id'), od=Count('id', filter=Q(is_overdue=True)))
    return {r[field]: (r['od'], r['n']) for r in rows}


def _pct(od, n):
    return od * 100.0 / n if n else 0.0


def _is_significant(cur_od, cur_n, base_od, base_n):
    if cur_n < conf.ALERT_MIN_N or base_n < conf.ALERT_MIN_N:
        return False
    cur, base = _pct(cur_od, cur_n), _pct(base_od, base_n)
    delta = cur - base
    if delta < conf.ALERT_MIN_DELTA_PP:
        return False
    return base == 0 or delta / base >= conf.ALERT_MIN_RELATIVE


def _concentrated_groups(qs, overall_rate, exclude_dims=(), top=3):
    """在目前期間內，找出逾期率高於整體、且 n ≥ ALERT_MIN_N 的前 top 個族群。"""
    groups = []
    for dim in CONCENTRATION_DIMENSIONS:
        if dim in exclude_dims:
            continue
        for value, (od, n) in _overdue_stats(qs, dim).items():
            if not value or n < conf.ALERT_MIN_N:
                continue
            rate = _pct(od, n)
            if rate > overall_rate:
                groups.append({
                    'dimension': dim,
                    'dimension_label': DIMENSION_LABELS[dim],
                    'value': value,
                    'label': _group_label(dim, value),
                    'rate': round(rate, 1),
                    'n': n,
                })
    groups.sort(key=lambda g: -g['rate'])
    return groups[:top]


def high_risk_groups(fact_qs, task_category=None, top=5):
    """
    逾期率高於整體、且 n ≥ ALERT_MIN_N 的族群（規格 §12.2 第 5 題）。
    與預警的「集中族群」用同一套邏輯，只是不需要先觸發預警。
    """
    qs = fact_qs.filter(is_required=True, is_due=True)
    if task_category:
        qs = qs.filter(task_category=task_category)
    n = qs.count()
    od = qs.filter(is_overdue=True).count()
    return {
        'overall': make_rate(od, n),
        'groups': _concentrated_groups(qs, _pct(od, n), top=top) if n else [],
    }


def _reminder_effect(qs):
    """到期前有收到提醒 vs 沒收到提醒的逾期率（相關性參考，非因果）。"""
    agg = qs.aggregate(
        r_n=Count('id', filter=Q(reminder_count__gt=0)),
        r_od=Count('id', filter=Q(reminder_count__gt=0, is_overdue=True)),
        nr_n=Count('id', filter=Q(reminder_count=0)),
        nr_od=Count('id', filter=Q(reminder_count=0, is_overdue=True)),
    )
    return {
        'reminded': make_rate(agg['r_od'], agg['r_n']),
        'not_reminded': make_rate(agg['nr_od'], agg['nr_n']),
    }


def _recommendation(category_label, alert):
    groups = [g['label'] for g in alert['concentrated_groups']]
    if alert['baseline_type'] == 'group':
        text = (
            f'{alert["current_label"]}的{category_label}逾期率為 {alert["current_rate"]:.1f}%，'
            f'高於{alert["baseline_label"]}的 {alert["baseline_rate"]:.1f}%'
            f'（+{alert["delta_pp"]:.1f} 個百分點）。'
            f'建議針對{alert["current_label"]}加強{category_label}的辦理提醒，並檢視相關說明是否清楚。'
        )
    else:
        target = '、'.join(groups) if groups else '本期學生'
        text = (
            f'{category_label}逾期率較{alert["baseline_label"]}上升 {alert["delta_pp"]:.1f} 個百分點'
            + (f'，主要集中在{"、".join(groups)}' if groups else '')
            + f'。建議針對{target}加強{category_label}的辦理提醒，並檢視相關說明是否清楚。'
        )

    effect = alert['reminder_effect']
    reminded, not_reminded = effect['reminded'], effect['not_reminded']
    # 差距太小（例如 11.1% 對 11.7%）不足以下「較低」的結論，至少要差 ALERT_MIN_DELTA_PP 個百分點才提
    if (not reminded['suppressed'] and not not_reminded['suppressed']
            and not_reminded['rate'] - reminded['rate'] >= conf.ALERT_MIN_DELTA_PP):
        text += (
            f'資料顯示，到期前收到提醒的學生逾期率較低（{reminded["rate"]:.1f}% 對 {not_reminded["rate"]:.1f}%），'
            '可優先確認上述學生都有收到提醒（此為相關性觀察，非因果結論）。'
        )
    return text


def _alert_for_category(qs):
    """qs：單一任務分類、已到期的必做任務。回傳 alert dict 或 None。"""
    # 1. 前一學年度
    years = {k: v for k, v in _overdue_stats(qs, 'academic_year').items() if k is not None}
    eligible_years = sorted(y for y, (_, n) in years.items() if n >= conf.ALERT_MIN_N)
    if eligible_years:
        cur_y = eligible_years[-1]
        if cur_y - 1 in years and years[cur_y - 1][1] >= conf.ALERT_MIN_N:
            (cur_od, cur_n), (base_od, base_n) = years[cur_y], years[cur_y - 1]
            if _is_significant(cur_od, cur_n, base_od, base_n):
                current_qs = qs.filter(academic_year=cur_y)
                return _build(current_qs, 'yoy', label_for('academic_year', cur_y), cur_od, cur_n,
                              label_for('academic_year', cur_y - 1), base_od, base_n)
            return None

    # 2. 上一個抵台梯次
    cohorts = {k: v for k, v in _overdue_stats(qs, 'arrival_cohort').items() if k}
    eligible_cohorts = sorted(c for c, (_, n) in cohorts.items() if n >= conf.ALERT_MIN_N)
    if len(eligible_cohorts) >= 2:
        cur_c, base_c = eligible_cohorts[-1], eligible_cohorts[-2]
        (cur_od, cur_n), (base_od, base_n) = cohorts[cur_c], cohorts[base_c]
        if _is_significant(cur_od, cur_n, base_od, base_n):
            current_qs = qs.filter(arrival_cohort=cur_c)
            return _build(current_qs, 'cohort', label_for('arrival_cohort', cur_c), cur_od, cur_n,
                          label_for('arrival_cohort', base_c), base_od, base_n,
                          exclude_dims=('arrival_cohort',))
        return None

    # 3. 單一時間點：找逾期率顯著高於整體的族群（取最嚴重的一個）
    total_n = qs.count()
    total_od = qs.filter(is_overdue=True).count()
    worst = None
    for dim in GROUP_DIMENSIONS:
        for value, (od, n) in _overdue_stats(qs, dim).items():
            if value and _is_significant(od, n, total_od, total_n):
                delta = _pct(od, n) - _pct(total_od, total_n)
                if worst is None or delta > worst[0]:
                    worst = (delta, dim, value, od, n)
    if worst:
        _, dim, value, od, n = worst
        current_qs = qs.filter(**{dim: value})
        return _build(current_qs, 'group', _group_label(dim, value), od, n, '整體', total_od, total_n,
                      skip_concentration=True)
    return None


def _build(current_qs, baseline_type, cur_label, cur_od, cur_n, base_label, base_od, base_n,
           exclude_dims=(), skip_concentration=False):
    cur_rate, base_rate = _pct(cur_od, cur_n), _pct(base_od, base_n)
    return {
        'baseline_type': baseline_type,
        'current_label': cur_label,
        'current_rate': round(cur_rate, 1),
        'current_n': cur_n,
        'baseline_label': base_label,
        'baseline_rate': round(base_rate, 1),
        'baseline_n': base_n,
        'delta_pp': round(cur_rate - base_rate, 1),
        'concentrated_groups': [] if skip_concentration else _concentrated_groups(current_qs, cur_rate, exclude_dims),
        'reminder_effect': _reminder_effect(current_qs),
    }


def compute_alerts(fact_qs):
    """對每個任務分類套用預警規則，回傳 alert dict 的 list（不寫資料庫）。"""
    due_qs = fact_qs.filter(is_required=True, is_due=True)
    alerts = []
    for code, label in TASK_CATEGORY_CHOICES:
        if code == 'other':
            continue
        alert = _alert_for_category(due_qs.filter(task_category=code))
        if alert:
            alert['task_category'] = code
            alert['recommendation'] = _recommendation(label, alert)
            alerts.append(alert)
    alerts.sort(key=lambda a: -a['delta_pp'])
    return alerts


def rebuild_alerts(snapshot_date, is_demo=False):
    """重建 InsightAlert：跨校（ALL）一份，每所學校各一份。回傳建立筆數。"""
    InsightAlert.objects.filter(is_demo=is_demo).delete()
    facts = FactStudentTask.objects.filter(is_demo=is_demo)

    scopes = [(ALL_SCHOOLS, facts)]
    for university in facts.values_list('university', flat=True).distinct().order_by('university'):
        scopes.append((university, facts.filter(university=university)))

    objs = []
    for university, qs in scopes:
        for alert in compute_alerts(qs):
            objs.append(InsightAlert(snapshot_date=snapshot_date, is_demo=is_demo, university=university, **alert))
    InsightAlert.objects.bulk_create(objs)
    return len(objs)


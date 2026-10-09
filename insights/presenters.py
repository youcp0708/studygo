"""
insights/presenters.py
把 AI 資料助理的工具查詢結果轉成畫面用的資料：中文標題、表格列、長條寬度、
是否被回答引用，以及延伸提問。不做任何計算，數字全部來自工具結果。
"""

import re

from .question_categories import QUESTION_CATEGORY_LABELS
from .task_categories import TASK_CATEGORY_LABELS

GROUP_LABELS = {
    'task_category': '任務分類',
    'identity_type': '身份別',
    'nationality': '國籍',
    'arrival_cohort': '抵台梯次',
    'academic_year': '學年度',
}

_NUMBER_RE = re.compile(r'\d+(?:\.\d+)?')


def _numbers_in(text):
    return {round(float(x), 1) for x in _NUMBER_RE.findall(text or '')}


def _cited(numbers, *values):
    """這一列的數字是否都出現在回答中（用來標出「回答引用」的列）。"""
    present = [v for v in values if v is not None]
    return bool(present) and all(round(float(v), 1) in numbers for v in present)


def _bar(value, maximum=100.0):
    if value is None or not maximum:
        return 0
    return max(2, min(100, round(value * 100.0 / maximum)))


# ── 各工具的呈現 ──
def _task_metrics(args, result, numbers):
    group = GROUP_LABELS.get(args.get('group_by'), '')
    rows = []
    for r in result['rows']:
        if not r['n']:
            continue
        rows.append({
            **r,
            'suppressed': r['overdue_rate'] is None,
            'bar': _bar(r['overdue_rate']),
            'cited': _cited(numbers, r['overdue_rate'], r['n']) or _cited(numbers, r['completion_rate'], r['n']),
        })
    # 任務分類維持流程順序；其他維度依逾期率由高到低，樣本不足的排最後
    if args.get('group_by') != 'task_category':
        rows.sort(key=lambda r: (r['suppressed'], -(r['overdue_rate'] or 0)))
    return {
        'kind': 'task_metrics',
        'title': f'{result["task_category"]}・依{group}的完成率與逾期率',
        'group_label': group,
        'rows': rows,
    }


def _question_rates(args, result, numbers):
    group = GROUP_LABELS.get(args.get('group_by'), '')
    maximum = max((r['per_100'] for r in result['rows'] if r['per_100'] is not None), default=0)
    rows = [
        {
            **r,
            'suppressed': r['per_100'] is None,
            'bar': _bar(r['per_100'], maximum),
            'cited': _cited(numbers, r['per_100'], r['students']),
        }
        for r in result['rows']
    ]
    return {
        'kind': 'question_rates',
        'title': f'「{result["category"]}」提問率・依{group}',
        'group_label': group,
        'rows': rows,
    }


def _compare_periods(args, result, numbers):
    code = args.get('task_category')
    rows = [
        {
            **r,
            'direction': 'up' if r['delta_pp'] > 0 else 'down' if r['delta_pp'] < 0 else 'flat',
            'delta_abs': abs(r['delta_pp']),
            'cited': _cited(numbers, r['current_rate'], r['current_n']) or _cited(numbers, abs(r['delta_pp'])),
        }
        for r in result['rows']
    ]
    title = f'{TASK_CATEGORY_LABELS[code]}・最近兩期的逾期率變化' if code else '各流程最近兩期的逾期率變化'
    return {'kind': 'compare_periods', 'title': title, 'rows': rows, 'not_comparable': result['not_comparable']}


def _high_risk_groups(args, result, numbers):
    overall = result['overall_rate']
    groups = [
        {
            **g,
            'diff': round(g['rate'] - overall, 1) if overall is not None else None,
            'bar': _bar(g['rate']),
            'cited': _cited(numbers, g['rate'], g['n']),
        }
        for g in result['groups']
    ]
    return {
        'kind': 'high_risk_groups',
        'title': f'{result["task_category"]}・逾期率偏高的族群',
        'overall_rate': overall,
        'overall_n': result['overall_n'],
        'overall_bar': _bar(overall),
        'groups': groups,
    }


def _list_alerts(args, result, numbers):
    return {'kind': 'list_alerts', 'title': '目前的風險預警', 'alerts': result['alerts']}


def _student_overview(args, result, numbers):
    def with_bar(rows):
        return [{**r, 'bar': _bar(r['pct'])} for r in rows]

    return {
        'kind': 'student_overview',
        'title': '學生概況',
        'total': result['total'],
        'academic_year': result['academic_year'],
        'new_students': result['new_students'],
        'by_identity': with_bar(result['by_identity']),
        'by_nationality': with_bar(result['by_nationality']),
    }


_PRESENTERS = {
    'task_metrics': _task_metrics,
    'question_rates': _question_rates,
    'compare_periods': _compare_periods,
    'high_risk_groups': _high_risk_groups,
    'list_alerts': _list_alerts,
    'student_overview': _student_overview,
}


def present_calls(calls, answer):
    """回傳畫面用的資料依據 list，順序與查詢順序相同。"""
    numbers = _numbers_in(answer)
    evidence = []
    for call in calls:
        result = call['result']
        presenter = _PRESENTERS.get(call['name'])
        if presenter is None or 'error' in result:
            item = {'kind': 'error', 'title': '這次查詢沒有成功', 'message': result.get('error', '未知的查詢')}
        else:
            item = presenter(call['arguments'], result, numbers)
        item['raw'] = call
        evidence.append(item)
    return evidence


# ══════════════════════════════════════════
# 延伸提問：依這次查了什麼，建議接下來可以問的問題（點了只會填入輸入框，不會直接送出）
# ══════════════════════════════════════════
def follow_ups(calls, limit=3):
    names = {c['name'] for c in calls}
    suggestions = []

    task_call = next((c for c in calls if c['name'] == 'task_metrics'), None)
    if task_call:
        code = task_call['arguments'].get('task_category')
        topic = TASK_CATEGORY_LABELS[code] if code else '各行政流程'
        used = task_call['arguments'].get('group_by')
        for group in ('nationality', 'identity_type', 'arrival_cohort'):
            if group != used:
                suggestions.append(f'改看依{GROUP_LABELS[group]}，{topic}的逾期率有什麼差異？')
                break

    question_call = next((c for c in calls if c['name'] == 'question_rates'), None)
    if question_call:
        category = QUESTION_CATEGORY_LABELS.get(question_call['arguments'].get('category'), '這類問題')
        suggestions.append(f'{category}的逾期率高嗎？和提問多寡有關係嗎？')

    if 'compare_periods' not in names:
        suggestions.append('和上一期相比，哪些流程的逾期率變差了？')
    if 'high_risk_groups' not in names:
        suggestions.append('哪些學生族群最需要加強行政提醒？')
    if 'list_alerts' not in names:
        suggestions.append('目前有哪些風險預警？')
    return suggestions[:limit]

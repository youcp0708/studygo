"""
insights/ask.py
AI 資料助理（規格 §12.3）與預設問題卡片（§12.4）。

設計原則：LLM 只負責「選分析工具」與「寫回答」，數字一律由 metrics.py / alerts.py 計算。
- LLM 不能寫 SQL、不能直接讀資料表。
- 工具參數沒有「學校」欄位：學校範圍由呼叫端依登入者決定（傳入的 data 已套用範圍）。
- 沒有任何回傳學生層級資料的工具。
"""

import json
import re

from django.conf import settings
from django.utils import timezone

from . import metrics
from .alerts import high_risk_groups
from .classify import llm_client
from .models import InsightAskLog
from .question_categories import QUESTION_CATEGORY_CHOICES, QUESTION_CATEGORY_CODES
from .task_categories import TASK_CATEGORY_CHOICES

MAX_TOOL_CALLS = 4
DAILY_LIMIT = 30
MAX_QUESTION_LENGTH = 500

TASK_CODES = [code for code, _ in TASK_CATEGORY_CHOICES if code != 'other']
TASK_GROUP_BY = ['task_category', 'identity_type', 'nationality', 'arrival_cohort', 'academic_year']
QUESTION_GROUP_BY = ['nationality', 'identity_type']

TOO_COMPLEX = '這個問題需要查詢的資料太多，請把問題拆成幾個比較小的問題再問一次。'
AI_UNAVAILABLE = 'AI 資料助理目前無法使用，請改用上方的預設問題。'


class ToolError(Exception):
    pass


# ══════════════════════════════════════════
# 分析工具
# 回傳值會原封不動送給 LLM，並顯示在畫面的「資料依據」中，所以只放聚合數字。
# ══════════════════════════════════════════
def _rate(r):
    return None if r is None or r['suppressed'] else r['rate']


def _check(value, allowed, name, nullable=False):
    if value is None and nullable:
        return None
    if value not in allowed:
        raise ToolError(f'{name} 不合法：{value}')
    return value


def tool_task_metrics(data, group_by, task_category=None):
    _check(group_by, TASK_GROUP_BY, 'group_by')
    _check(task_category, TASK_CODES, 'task_category', nullable=True)
    qs = data['fact'].filter(task_category=task_category) if task_category else data['fact']
    rows = metrics.task_metrics_by(qs, group_by)
    return {
        'group_by': group_by,
        'task_category': metrics.label_for('task_category', task_category) if task_category else '全部任務',
        'rows': [
            {
                'value': r['value'],
                'label': r['label'],
                'completion_rate': _rate(r['completion']),
                'overdue_rate': _rate(r['overdue']),
                'n': r['completion']['n'],
                'note': '樣本不足' if r['completion']['suppressed'] else '',
            }
            for r in rows
        ],
    }


def tool_question_rates(data, group_by, category):
    _check(group_by, QUESTION_GROUP_BY, 'group_by')
    _check(category, QUESTION_CATEGORY_CODES, 'category')
    rows = metrics.question_rate_by(data['questions'], data['dim'], group_by, category)
    return {
        'group_by': group_by,
        'category': metrics.label_for('category', category),
        'rows': [
            {
                'label': r['label'],
                'students': r['students'],
                'questions': r['questions'],
                'per_100': r['per_100'],
                'note': '樣本不足' if r['suppressed'] else '',
            }
            for r in rows
        ],
    }


def tool_compare_periods(data, task_category=None):
    _check(task_category, TASK_CODES, 'task_category', nullable=True)
    rows = metrics.compare_periods(data['fact'], task_category)
    period_names = {'academic_year': '學年度', 'arrival_cohort': '抵台梯次'}
    return {
        'rows': [
            {
                'label': r['label'],
                'period_type': period_names[r['period_type']],
                'baseline_label': r['baseline_label'],
                'baseline_rate': r['baseline']['rate'],
                'baseline_n': r['baseline']['n'],
                'current_label': r['current_label'],
                'current_rate': r['current']['rate'],
                'current_n': r['current']['n'],
                'delta_pp': r['delta_pp'],
            }
            for r in rows if r['delta_pp'] is not None
        ],
        'not_comparable': [r['label'] for r in rows if r['delta_pp'] is None],
    }


def tool_high_risk_groups(data, task_category=None):
    _check(task_category, TASK_CODES, 'task_category', nullable=True)
    result = high_risk_groups(data['fact'], task_category)
    return {
        'task_category': metrics.label_for('task_category', task_category) if task_category else '全部任務',
        'overall_rate': _rate(result['overall']),
        'overall_n': result['overall']['n'],
        'groups': [
            {'label': g['label'], 'dimension': g['dimension_label'], 'rate': g['rate'], 'n': g['n']}
            for g in result['groups']
        ],
    }


def tool_list_alerts(data):
    return {
        'alerts': [
            {
                'task_category': a.get_task_category_display(),
                'baseline_type': a.get_baseline_type_display(),
                'current_label': a.current_label,
                'current_rate': a.current_rate,
                'current_n': a.current_n,
                'baseline_label': a.baseline_label,
                'baseline_rate': a.baseline_rate,
                'baseline_n': a.baseline_n,
                'delta_pp': a.delta_pp,
                'groups': [{'label': g['label'], 'rate': g['rate'], 'n': g['n']} for g in a.concentrated_groups],
                'recommendation': a.recommendation,
            }
            for a in data['alerts']
        ],
    }


def tool_student_overview(data):
    overview = metrics.student_overview(data['dim'], timezone.localdate())

    def compact(rows):
        return [{'label': r['label'], 'count': r['count'], 'pct': r['pct']} for r in rows]

    return {
        'total': overview['total'],
        'academic_year': overview['academic_year'],
        'new_students': overview['new_students'],
        'by_identity': compact(overview['by_identity']),
        'by_nationality': compact(overview['by_nationality']),
    }


TOOL_FUNCS = {
    'task_metrics': tool_task_metrics,
    'question_rates': tool_question_rates,
    'compare_periods': tool_compare_periods,
    'high_risk_groups': tool_high_risk_groups,
    'list_alerts': tool_list_alerts,
    'student_overview': tool_student_overview,
}


def run_tool(name, args, data):
    """執行分析工具。參數不合法時回傳 {'error': ...}，讓 LLM 自行修正。"""
    func = TOOL_FUNCS.get(name)
    if func is None:
        return {'error': f'沒有這個工具：{name}'}
    try:
        return func(data, **args)
    except (ToolError, TypeError) as e:
        return {'error': str(e)}


# ── 給 OpenAI 的工具定義（strict 模式：所有參數必填，選填參數以 null 表示）──
def _nullable_enum(values, description):
    return {'type': ['string', 'null'], 'enum': values + [None], 'description': description}


def _function(name, description, properties=None):
    properties = properties or {}
    return {
        'type': 'function',
        'name': name,
        'description': description,
        'strict': True,
        'parameters': {
            'type': 'object',
            'properties': properties,
            'required': list(properties),
            'additionalProperties': False,
        },
    }


_TASK_CATEGORY_DESC = '任務分類代碼；null 代表全部任務。' + '、'.join(
    f'{c}={label}' for c, label in TASK_CATEGORY_CHOICES if c != 'other')

TOOLS = [
    _function(
        'task_metrics',
        '依某個維度分組，回傳必做任務的完成率與逾期率（只算已到期任務）及分母 n。',
        {
            'group_by': {'type': 'string', 'enum': TASK_GROUP_BY, 'description': '分組維度'},
            'task_category': _nullable_enum(TASK_CODES, _TASK_CATEGORY_DESC),
        },
    ),
    _function(
        'question_rates',
        '依國籍或身份別分組，回傳某類提問的「每 100 名學生提問數」。跨族群比較提問多寡時一律用這個工具。',
        {
            'group_by': {'type': 'string', 'enum': QUESTION_GROUP_BY, 'description': '分組維度'},
            'category': {
                'type': 'string', 'enum': QUESTION_CATEGORY_CODES,
                'description': '提問分類代碼：' + '、'.join(f'{c}={label}' for c, label in QUESTION_CATEGORY_CHOICES),
            },
        },
    ),
    _function(
        'compare_periods',
        '比較各任務分類最近兩個期間（優先學年度，不足時用抵台梯次）的逾期率，delta_pp 為負代表改善。',
        {'task_category': _nullable_enum(TASK_CODES, _TASK_CATEGORY_DESC)},
    ),
    _function(
        'high_risk_groups',
        '找出逾期率高於整體、且分母 n ≥ 30 的族群（身份別、國籍、抵台梯次）。',
        {'task_category': _nullable_enum(TASK_CODES, _TASK_CATEGORY_DESC)},
    ),
    _function('list_alerts', '列出目前的風險預警（逾期率顯著上升或偏高的任務）。'),
    _function('student_overview', '學生總數、本學年度新生數、身份別與國籍分布。'),
]


INSTRUCTIONS = """你是 ReadyTo Taiwan 的 Student Insights 資料分析助理，服務對象是大學國際處／境外生組的行政人員。
你只能根據分析工具回傳的結果回答，不可以推測、估算或編造任何數字。

【指標定義】
- 只計算必做任務。完成率 = 已到期且已完成 ÷ 已到期；逾期率 = 逾期 ÷ 已到期。未到期的任務不列入。
- 比較不同國籍或身份別的提問多寡時，一律用「每 100 名學生提問數」，不可以只比次數。
- 「居留證件」包含 ARC、臺灣地區居留證、港澳生的居留入出境證。使用者說「ARC」時查詢居留證件，並提醒港澳生辦理的證件不同。
- 學年度為民國年、8/1 起算；抵台梯次是學生填寫的預計抵台年月。

【回答規則】
1. 每個比率都要附上分母，格式例如「13.6%（n=214）」。數字必須與工具結果完全相同，不要自行四捨五入或換算。
2. 工具結果為 null 或註明「樣本不足」的項目，回答「樣本不足」，不要給數字。
3. 只回答族群層級的結果。被要求提供個別學生資料時，說明基於個資保護無法提供。
4. 「為什麼」類問題只描述資料中觀察到的差異，並註明「此為相關性觀察，非因果結論」。
5. 提出建議時，每一句都要對應到你引用的數字；資料中找不到依據的具體做法不要提出。
6. 工具結果不足以回答時，直接說「目前資料不足以回答」，並說明缺少什麼。
7. 使用繁體中文，簡潔回答，不要使用 Markdown 表格。
"""


def build_instructions(context):
    return INSTRUCTIONS + (
        f'\n【本次查詢範圍】\n'
        f'- 學校：{context["school_label"]}\n'
        f'- 篩選條件：{context["filter_label"]}\n'
        f'- 資料日期：{context["snapshot_date"] or "尚未產生"}\n'
        + ('- 注意：目前是「示範資料」，回答開頭請註明。\n' if context['is_demo'] else '')
    )


# ══════════════════════════════════════════
# 數字驗證
# ══════════════════════════════════════════
_PCT_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(?:%|％|個百分點)')
_N_RE = re.compile(r'n\s*[=＝]\s*(\d+)', re.I)


def _collect_numbers(value, out):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out.add(round(abs(float(value)), 1))
    elif isinstance(value, dict):
        for v in value.values():
            _collect_numbers(v, out)
    elif isinstance(value, list):
        for v in value:
            _collect_numbers(v, out)


def verify_numbers(answer, calls):
    """回答中的百分比、百分點、n 是否都出現在工具結果中。回傳 (是否通過, 找不到的數字)。"""
    allowed = set()
    for call in calls:
        _collect_numbers(call['result'], allowed)
    found = _PCT_RE.findall(answer) + _N_RE.findall(answer)
    unverified = [x for x in found if round(float(x), 1) not in allowed]
    return not unverified, unverified


# ══════════════════════════════════════════
# AI 問答
# ══════════════════════════════════════════
def ask_llm(question, data, context, client, model):
    """回傳 (回答, 工具呼叫紀錄)。工具呼叫超過 MAX_TOOL_CALLS 時回傳 TOO_COMPLEX。"""
    instructions = build_instructions(context)
    input_items = [{'role': 'user', 'content': question}]
    calls = []
    while True:
        response = client.responses.create(model=model, instructions=instructions, input=input_items, tools=TOOLS)
        function_calls = [item for item in response.output if getattr(item, 'type', '') == 'function_call']
        if not function_calls:
            return (response.output_text or '').strip(), calls
        if len(calls) + len(function_calls) > MAX_TOOL_CALLS:
            return TOO_COMPLEX, calls

        input_items += response.output
        for fc in function_calls:
            try:
                args = json.loads(fc.arguments or '{}')
            except json.JSONDecodeError:
                args = {}
            result = run_tool(fc.name, args, data)
            calls.append({'name': fc.name, 'arguments': args, 'result': result})
            input_items.append({
                'type': 'function_call_output',
                'call_id': fc.call_id,
                'output': json.dumps(result, ensure_ascii=False),
            })


# ══════════════════════════════════════════
# 預設問題卡片（不經過 LLM，作為 AI 回答的驗收基準）
# ══════════════════════════════════════════
def _fmt(rate, n):
    return f'{rate}%（n={n}）'


def _call(name, args, data, calls):
    result = run_tool(name, args, data)
    calls.append({'name': name, 'arguments': args, 'result': result})
    return result


def _preset_residence_overdue(data, calls):
    parts = []
    for group_by, word in (('identity_type', '身份別'), ('nationality', '國籍')):
        rows = _call('task_metrics', {'group_by': group_by, 'task_category': 'residence_permit'}, data, calls)['rows']
        rows = [r for r in rows if r['overdue_rate'] is not None]
        if rows:
            top = max(rows, key=lambda r: r['overdue_rate'])
            label = f'{top["label"]}籍' if group_by == 'nationality' else top['label']
            parts.append(f'{word}是{label}：{_fmt(top["overdue_rate"], top["n"])}')
        else:
            parts.append(f'{word}：樣本不足')
    return ('居留證件逾期率最高的' + '；'.join(parts) + '。'
            '（居留證件包含 ARC、臺灣地區居留證與港澳生的居留入出境證。）')


def _preset_lowest_completion(data, calls):
    rows = _call('task_metrics', {'group_by': 'task_category', 'task_category': None}, data, calls)['rows']
    rows = sorted((r for r in rows if r['value'] != 'other' and r['completion_rate'] is not None),
                  key=lambda r: r['completion_rate'])
    if not rows:
        return '目前資料不足以回答：沒有任何任務分類的已到期任務數達到 10 筆。'
    text = f'目前完成率最低的是「{rows[0]["label"]}」：{_fmt(rows[0]["completion_rate"], rows[0]["n"])}。'
    if len(rows) > 1:
        text += '其次：' + '、'.join(f'{r["label"]} {_fmt(r["completion_rate"], r["n"])}' for r in rows[1:3]) + '。'
    return text + '（完成率只計算已過截止日的必做任務。）'


def _preset_residence_questions(data, calls):
    rows = _call('question_rates', {'group_by': 'nationality', 'category': 'residence_permit'}, data, calls)['rows']
    rows = [r for r in rows if r['per_100'] is not None]
    if not rows:
        return '目前資料不足以回答：沒有任何國籍的學生人數達到 10 人。'
    top = rows[0]
    text = f'每 100 名學生詢問居留證件次數最多的是{top["label"]}籍：{top["per_100"]} 次（學生 n={top["students"]}）。'
    if len(rows) > 1:
        text += '其次：' + '、'.join(f'{r["label"]}籍 {r["per_100"]} 次（學生 n={r["students"]}）' for r in rows[1:3]) + '。'
    return text


def _preset_most_improved(data, calls):
    result = _call('compare_periods', {'task_category': None}, data, calls)
    rows = result['rows']
    if not rows:
        return '目前資料不足以回答：沒有任何任務分類同時具備兩個期間、且各期間至少 10 筆已到期任務。'
    best = rows[0]
    change = (f'{best["baseline_label"]} {_fmt(best["baseline_rate"], best["baseline_n"])} → '
              f'{best["current_label"]} {_fmt(best["current_rate"], best["current_n"])}')
    if best['delta_pp'] < 0:
        return f'逾期率下降最多的是「{best["label"]}」：{change}，下降 {abs(best["delta_pp"])} 個百分點。'
    return f'目前沒有任何流程的逾期率下降。變化最小的是「{best["label"]}」：{change}（+{best["delta_pp"]} 個百分點）。'


def _preset_reminder_groups(data, calls):
    risk = _call('high_risk_groups', {'task_category': None}, data, calls)
    alerts = _call('list_alerts', {}, data, calls)['alerts']
    if risk['overall_rate'] is None:
        return '目前資料不足以回答：已到期任務不到 10 筆。'
    text = f'整體逾期率為 {_fmt(risk["overall_rate"], risk["overall_n"])}。'
    if risk['groups']:
        text += '逾期率高於整體、且樣本足夠（n ≥ 30）的族群：' + '、'.join(
            f'{g["label"]} {_fmt(g["rate"], g["n"])}' for g in risk['groups']) + '，建議優先加強這些族群的行政提醒。'
    else:
        text += '目前沒有逾期率高於整體且樣本足夠（n ≥ 30）的族群。'
    if alerts:
        text += f'另有 {len(alerts)} 則風險預警：' + '、'.join(
            f'{a["task_category"]}（{a["current_label"]}）' for a in alerts) + '，詳見「風險預警」頁。'
    return text


PRESETS = [
    {'id': 1, 'question': '哪種身份別／國籍的學生，居留證件逾期率最高？', 'func': _preset_residence_overdue},
    {'id': 2, 'question': '哪一個行政任務完成率最低？', 'func': _preset_lowest_completion},
    {'id': 3, 'question': '哪個國籍的學生，每 100 人詢問居留證件的次數最多？', 'func': _preset_residence_questions},
    {'id': 4, 'question': '和上一個比較期間相比，哪個行政流程的逾期率下降最多？', 'func': _preset_most_improved},
    {'id': 5, 'question': '哪些學生族群需要更多行政提醒？', 'func': _preset_reminder_groups},
]
PRESETS_BY_ID = {p['id']: p for p in PRESETS}


# ══════════════════════════════════════════
# 對外入口
# ══════════════════════════════════════════
def remaining_quota(user):
    today = timezone.localdate()
    used = InsightAskLog.objects.filter(
        user=user, source__in=('llm', 'error'), created_at__date=today,
    ).count()
    return max(DAILY_LIMIT - used, 0)


def ai_available():
    return bool(getattr(settings, 'OPENAI_API_KEY', None))


def answer_preset(user, scope, data, preset_id):
    preset = PRESETS_BY_ID[preset_id]
    calls = []
    answer = preset['func'](data, calls)
    InsightAskLog.objects.create(user=user, scope=scope, question=preset['question'], tool_calls=calls,
                                 answer=answer, source='preset', verified=True)
    return {'question': preset['question'], 'answer': answer, 'calls': calls, 'source': 'preset',
            'verified': True, 'unverified': []}


def answer_question(user, scope, data, context, question, client=None):
    """AI 問答。呼叫端需先確認 remaining_quota(user) > 0。"""
    client = client or llm_client()
    if client is None:
        return {'question': question, 'answer': AI_UNAVAILABLE, 'calls': [], 'source': 'error',
                'verified': True, 'unverified': []}
    try:
        answer, calls = ask_llm(question, data, context, client, getattr(settings, 'OPENAI_MODEL', None))
        source = 'llm'
    except Exception:
        answer, calls, source = AI_UNAVAILABLE, [], 'error'

    verified, unverified = verify_numbers(answer, calls)
    InsightAskLog.objects.create(user=user, scope=scope, question=question, tool_calls=calls,
                                 answer=answer, source=source, verified=verified)
    return {'question': question, 'answer': answer, 'calls': calls, 'source': source,
            'verified': verified, 'unverified': unverified}

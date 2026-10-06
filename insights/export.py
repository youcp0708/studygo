"""
insights/export.py
CSV 匯出（規格 §12.5）。只匯出聚合結果，不提供學生層級資料。
- 分母 < MIN_DISPLAY_N 的格子：比率留空、n 顯示「<10」，備註「樣本不足」。
- 第一列註明資料日期、範圍，以及「去識別化統計資料，請勿外流」。
"""

import csv
import io

from . import conf, metrics

EXPORTS = {
    'tasks': '任務完成率與逾期率',
    'questions': '學生提問率',
    'alerts': '風險預警',
}

_TASK_FIELDS = ['task_category', 'identity_type', 'nationality', 'arrival_cohort']
_QUESTION_FIELDS = ['nationality', 'identity_type']
_SMALL_N = f'<{conf.MIN_DISPLAY_N}'


def _n(rate):
    return _SMALL_N if rate['suppressed'] else rate['n']


def _rate(rate):
    return '' if rate['suppressed'] else rate['rate']


def _task_rows(data):
    yield ['任務分類', '身份別', '國籍', '抵台梯次', '已到期任務數（n）', '完成率（%）', '逾期率（%）', '備註']
    for r in metrics.task_metrics_grouped(data['fact'], _TASK_FIELDS):
        labels = r['labels']
        yield [
            labels['task_category'], labels['identity_type'], labels['nationality'], labels['arrival_cohort'],
            _n(r['completion']), _rate(r['completion']), _rate(r['overdue']),
            '樣本不足' if r['completion']['suppressed'] else '',
        ]


def _question_rows(data):
    yield ['提問分類', '國籍', '身份別', '學生數', '提問數', '每 100 名學生提問數', '備註']
    for r in metrics.question_rates_grouped(data['questions'], data['dim'], _QUESTION_FIELDS):
        small = r['suppressed']
        yield [
            r['category_label'], r['labels']['nationality'], r['labels']['identity_type'],
            _SMALL_N if small else r['students'],
            _SMALL_N if small else r['questions'],
            '' if small else r['per_100'],
            '樣本不足' if small else '',
        ]


def _alert_rows(data):
    yield ['任務分類', '比較基準', '目前期間／族群', '目前逾期率（%）', '目前 n',
           '基準期間／族群', '基準逾期率（%）', '基準 n', '變化（百分點）', '逾期集中族群', '行動建議']
    for a in data['alerts']:
        groups = '、'.join(f'{g["label"]} {g["rate"]}%（n={g["n"]}）' for g in a.concentrated_groups)
        yield [
            a.get_task_category_display(), a.get_baseline_type_display(),
            a.current_label, a.current_rate, a.current_n,
            a.baseline_label, a.baseline_rate, a.baseline_n,
            a.delta_pp, groups, a.recommendation,
        ]


_BUILDERS = {'tasks': _task_rows, 'questions': _question_rows, 'alerts': _alert_rows}


def build_csv(name, data, header):
    """回傳 CSV 字串（含 UTF-8 BOM，Excel 開啟中文才不會亂碼）。"""
    buffer = io.StringIO()
    buffer.write('﻿')
    writer = csv.writer(buffer)
    writer.writerow([header])
    writer.writerows(_BUILDERS[name](data))
    return buffer.getvalue()

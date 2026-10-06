"""
insights/views.py
校方端 Student Insights 頁面。所有頁面都只讀分析表（insights_*）。
"""

from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from . import ask as ask_service
from . import conf, export, metrics, services
from .permissions import ALL_SCHOOLS, insights_access_required
from .question_categories import QUESTION_CATEGORY_CHOICES
from .task_categories import TASK_CATEGORY_CHOICES, TASK_CATEGORY_LABELS


def _context(request, active):
    scope = request.insights_scope
    filters = services.parse_filters(request.GET, scope)
    data = services.datasets(scope, filters)
    school = data['school']
    return data, {
        'active': active,
        'scope': scope,
        'is_all_schools': scope == ALL_SCHOOLS,
        'school_label': metrics.label_for('university', school) if school else '全部學校',
        'filters': filters,
        'filter_options': services.filter_options(scope, filters),
        'query_string': request.GET.urlencode(),
        'snapshot_date': services.snapshot_date(),
        'is_demo': conf.use_demo_data(),
        'min_display_n': conf.MIN_DISPLAY_N,
    }


@insights_access_required
def dashboard(request):
    data, ctx = _context(request, 'dashboard')
    ctx.update({
        'overview': metrics.student_overview(data['dim'], timezone.localdate()),
        'task_summary': metrics.task_summary(data['fact']),
        'task_rows': metrics.task_metrics_by(data['fact'], 'task_category'),
        'alerts': data['alerts'][:3],
        'alert_total': data['alerts'].count(),
    })
    return render(request, 'insights/dashboard.html', ctx)


@insights_access_required
def tasks(request):
    data, ctx = _context(request, 'tasks')
    category = request.GET.get('category')
    if category not in TASK_CATEGORY_LABELS:
        category = 'residence_permit'
    category_fact = data['fact'].filter(task_category=category)
    ctx.update({
        'category': category,
        'category_label': TASK_CATEGORY_LABELS[category],
        'category_choices': [c for c in TASK_CATEGORY_CHOICES if c[0] != 'other'],
        'task_summary': metrics.task_summary(data['fact']),
        'task_rows': metrics.task_metrics_by(data['fact'], 'task_category'),
        'by_identity': metrics.task_metrics_by(category_fact, 'identity_type'),
        'by_nationality': metrics.task_metrics_by(category_fact, 'nationality'),
        'trend': metrics.overdue_trend_by_cohort(data['fact'], category),
    })
    return render(request, 'insights/tasks.html', ctx)


@insights_access_required
def alerts(request):
    data, ctx = _context(request, 'alerts')
    ctx['alerts'] = data['alerts']
    return render(request, 'insights/alerts.html', ctx)


@insights_access_required
def questions(request):
    data, ctx = _context(request, 'questions')
    valid = {code for code, _ in QUESTION_CATEGORY_CHOICES}
    category = request.GET.get('category')
    if category not in valid:
        category = 'residence_permit'
    ctx.update({
        'category': category,
        'category_label': metrics.label_for('category', category),
        'category_choices': QUESTION_CATEGORY_CHOICES,
        'share': metrics.question_share(data['questions']),
        'rate_by_nationality': metrics.question_rate_by(data['questions'], data['dim'], 'nationality', category),
        'rate_by_identity': metrics.question_rate_by(data['questions'], data['dim'], 'identity_type', category),
        'needs': metrics.needs_vs_overdue(data['questions'], data['dim'], data['fact']),
    })
    return render(request, 'insights/questions.html', ctx)


@insights_access_required
@require_http_methods(['GET', 'POST'])
def ask(request):
    data, ctx = _context(request, 'ask')
    scope = request.insights_scope
    result, error = None, None

    if request.method == 'POST':
        question = request.POST.get('question', '').strip()[:ask_service.MAX_QUESTION_LENGTH]
        if not question:
            error = '請輸入問題。'
        elif ask_service.remaining_quota(request.user) <= 0:
            error = f'今天的提問次數已達上限（{ask_service.DAILY_LIMIT} 題），請改用預設問題或明天再試。'
        else:
            filter_label = '、'.join(
                metrics.label_for(k if k != 'school' else 'university', v) for k, v in ctx['filters'].items()
            ) or '無'
            context = {
                'school_label': ctx['school_label'],
                'filter_label': filter_label,
                'snapshot_date': ctx['snapshot_date'],
                'is_demo': ctx['is_demo'],
            }
            result = ask_service.answer_question(request.user, scope, data, context, question)
    elif request.GET.get('preset'):
        try:
            preset_id = int(request.GET['preset'])
        except ValueError:
            preset_id = None
        if preset_id in ask_service.PRESETS_BY_ID:
            result = ask_service.answer_preset(request.user, scope, data, preset_id)

    ctx.update({
        'presets': ask_service.PRESETS,
        'result': result,
        'error': error,
        'ai_available': ask_service.ai_available(),
        'remaining_quota': ask_service.remaining_quota(request.user),
        'daily_limit': ask_service.DAILY_LIMIT,
    })
    return render(request, 'insights/ask.html', ctx)


@insights_access_required
def export_csv(request, name):
    if name not in export.EXPORTS:
        raise Http404
    data, ctx = _context(request, 'export')
    header = (
        f'{export.EXPORTS[name]}｜{ctx["school_label"]}｜'
        f'資料日期 {ctx["snapshot_date"] or "尚未產生"}'
        + ('｜示範資料' if ctx['is_demo'] else '')
        + '｜去識別化統計資料，請勿外流'
    )
    response = HttpResponse(export.build_csv(name, data, header), content_type='text/csv; charset=utf-8')
    filename = f'insights_{name}_{ctx["snapshot_date"] or "nodata"}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

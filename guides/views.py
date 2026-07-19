import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import translation

logger = logging.getLogger(__name__)


@login_required(login_url='/login/')
def guide_index(request):
    return render(request, 'guides/guide_index.html')

@login_required(login_url='/login/')
def guide_regulations(request):
    return render(request, 'guides/guide_regulations.html')

@login_required(login_url='/login/')
def admissions_guide(request):
    return render(request, 'guides/admissions_guide.html')

@login_required(login_url='/login/')
def guide_national_area(request):
    return render(request, 'guides/guide_national_area.html')

@login_required(login_url='/login/')
def guide_arc_exchange(request):
    return render(request, 'guides/guide_arc_exchange.html')

@login_required(login_url='/login/')
def guide_arc_foreign(request):
    return render(request, 'guides/guide_arc_foreign.html')

@login_required(login_url='/login/')
def guide_arc_overseas(request):
    return render(request, 'guides/guide_arc_overseas.html')

@login_required(login_url='/login/')
def guide_bus_ncu(request):
    return render(request, 'guides/guide_bus_ncu.html')

@login_required(login_url='/login/')
def guide_housing_ncu(request):
    return render(request, 'guides/guide_housing_ncu.html')

@login_required(login_url='/login/')
def guide_nhi(request):
    return render(request, 'guides/guide_nhi.html')

@login_required(login_url='/login/')
def guide_bank(request):
    return render(request, 'guides/guide_bank.html')

@login_required(login_url='/login/')
def guide_sim(request):
    return render(request, 'guides/guide_sim.html')

@login_required(login_url='/login/')
def guide_work_permit(request):
    return render(request, 'guides/guide_work_permit.html')

@login_required(login_url='/login/')
def guide_medical(request):
    return render(request, 'guides/guide_medical.html')

@login_required(login_url='/login/')
def guide_course(request):
    return render(request, 'guides/guide_course.html')

@login_required(login_url='/login/')
def guide_graduation(request):
    return render(request, 'guides/guide_graduation.html')

@login_required(login_url='/login/')
def guide_admin_docs(request):
    # 學校名稱 → code 對應表，之後加學校在這裡新增
    SCHOOL_MAP = {
        '國立中央大學': 'ncu',
        'National Central University': 'ncu',
        'NCU': 'ncu',
    }
    # 目前僅開放 NCU，查不到對應時一律退回 NCU，避免頁面拿到 'unknown' 而顯示空白
    school_code = 'ncu'
    school_name = ''
    try:
        university = request.user.student_profile.university or ''
        school_code = SCHOOL_MAP.get(university.strip(), 'ncu')
        school_name = university
    except Exception:
        logger.debug('guide_admin_docs: user %s 尚無 student_profile', request.user.id, exc_info=True)
    return render(request, 'guides/guide_admin_docs.html', {
        'school_code': school_code,
        'school_name': school_name,
    })

@login_required(login_url='/login/')
def guide_scholarship(request):
    return render(request, 'guides/guide_scholarship.html')

@login_required(login_url='/login/')
def guide_mental_health(request):
    return render(request, 'guides/guide_mental_health.html')

@login_required(login_url='/login/')
def guide_enrollment(request):
    return render(request, 'guides/guide_enrollment.html')

@login_required(login_url='/login/')
def guide_library(request):
    return render(request, 'guides/guide_library.html')

@login_required(login_url='/login/')
def guide_emergency(request):
    return render(request, 'guides/guide_emergency.html')

@login_required(login_url='/login/')
def guide_systems(request):
    return render(request, 'guides/guide_systems.html')

@login_required(login_url='/login/')
def guide_map(request):
    from django.conf import settings
    from django.utils import translation
    lang_map = {
        'zh-hant': 'zh-TW', 'en': 'en', 'id': 'id',
        'ja': 'ja', 'ms': 'ms', 'my': 'my', 'th': 'th',
    }
    current_lang = (translation.get_language() or 'zh-hant').lower()
    return render(request, 'guides/guide_map.html', {
        'maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'maps_lang': lang_map.get(current_lang, 'zh-TW'),
    })


@login_required(login_url='/login/')
def guide_search(request):
    from .search_data import SEARCH_BODY
    q = request.GET.get('q', '').strip()
    lang = (translation.get_language() or 'zh-hant').lower()
    body = {}
    for url, langs in SEARCH_BODY.items():
        body[url] = langs.get(lang) or langs.get('en') or langs.get('zh-hant') or []
    return render(request, 'guides/guide_search.html', {
        'q': q,
        'body_data': body,
    })

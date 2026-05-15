from django.contrib.auth.decorators import login_required
from django.shortcuts import render


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

"""
flow/urls.py
前端頁面路由 — 掛載於 studygo/urls.py → path('', include('flow.urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    path('flow/', views.flow_page, name='flow_page'),
    path('flow/guide/arc-overseas/', views.guide_arc_overseas, name='guide_arc_overseas'),
    path('flow/guide/arc-foreign/',  views.guide_arc_foreign,  name='guide_arc_foreign'),
    path('flow/guide/arc-exchange/', views.guide_arc_exchange, name='guide_arc_exchange'),
    path('flow/guide/bus-ncu/',      views.guide_bus_ncu,      name='guide_bus_ncu'),
    path('flow/guide/housing-ncu/', views.guide_housing_ncu,  name='guide_housing_ncu'),
]

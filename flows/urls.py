from django.urls import path
from . import views

urlpatterns = [
    # 前端網頁路由
    path('my-tasks/', views.my_flows_page, name='my_flows'),

    # 指南頁面
    path('guides/', views.guide_index, name='guide_index'),
    path('guides/regulations/', views.guide_regulations, name='guide_regulations'),
    path('guides/arc-exchange/',  views.guide_arc_exchange,  name='guide_arc_exchange'),
    path('guides/arc-foreign/',   views.guide_arc_foreign,   name='guide_arc_foreign'),
    path('guides/arc-overseas/',  views.guide_arc_overseas,  name='guide_arc_overseas'),
    path('guides/bus-ncu/',       views.guide_bus_ncu,       name='guide_bus_ncu'),
    path('guides/housing-ncu/',   views.guide_housing_ncu,   name='guide_housing_ncu'),
    path('guides/admissions/',    views.admissions_guide,    name='admissions_guide'),
]

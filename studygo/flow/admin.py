from django.contrib import admin
from .models import FlowStepTemplate, ProcessFlow, UserTask


@admin.register(FlowStepTemplate)
class FlowStepTemplateAdmin(admin.ModelAdmin):
    list_display  = ('title', 'category', 'order', 'is_required', 'is_active', 'days_offset')
    list_filter   = ('category', 'is_required', 'is_active')
    search_fields = ('title', 'description')
    ordering      = ('order',)


class UserTaskInline(admin.TabularInline):
    model          = UserTask
    extra          = 0
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    fields         = ('title', 'category', 'status', 'is_required',
                      'due_date', 'completed_at', 'order')


@admin.register(ProcessFlow)
class ProcessFlowAdmin(admin.ModelAdmin):
    list_display   = ('user', 'identity_type', 'admission_status', 'created_at')
    list_filter    = ('identity_type', 'admission_status')
    search_fields  = ('user__email', 'user__name')
    inlines        = [UserTaskInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display   = ('user', 'title', 'category', 'status', 'due_date', 'is_required')
    list_filter    = ('status', 'category', 'is_required')
    search_fields  = ('user__email', 'user__name', 'title')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    ordering       = ('user', 'order')

from django.contrib import admin
from .models import FlowStage, Task, StudentTask

@admin.register(FlowStage)
class FlowStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'stage', 'identity_type', 'nationality', 'is_required', 'order')
    list_filter = ('stage', 'identity_type', 'nationality', 'is_required')
    ordering = ('stage__order', 'order')

@admin.register(StudentTask)
class StudentTaskAdmin(admin.ModelAdmin):
    list_display = ('student', 'task', 'status', 'completed_at')
    list_filter = ('status', 'task__stage')
    search_fields = ('student__user__name', 'student__user__email', 'task__title')



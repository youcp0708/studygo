from django.contrib import admin
from .models import FlowStage, Task, StudentTask, Reminder


@admin.register(FlowStage)
class FlowStageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'name_en',
        'name_my',
        'name_id',
        'name_ms',
        'name_th',
        'name_ja',
        'order',
    )

    fieldsets = (
        ('基本資料', {
            'fields': (
                'name',
                'description',
                'order',
            )
        }),
        ('英文 English', {
            'fields': (
                'name_en',
                'description_en',
            )
        }),
        ('緬甸語 Burmese', {
            'fields': (
                'name_my',
                'description_my',
            )
        }),
        ('印尼語 Indonesian', {
            'fields': (
                'name_id',
                'description_id',
            )
        }),
        ('馬來語 Malay', {
            'fields': (
                'name_ms',
                'description_ms',
            )
        }),
        ('泰語 Thai', {
            'fields': (
                'name_th',
                'description_th',
            )
        }),
        ('日語 Japanese', {
            'fields': (
                'name_ja',
                'description_ja',
            )
        }),
    )

    search_fields = (
        'name',
        'name_en',
        'name_my',
        'name_id',
        'name_ms',
        'name_th',
        'name_ja',
    )

    ordering = ('order',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'title_en',
        'title_my',
        'title_id',
        'title_ms',
        'title_th',
        'title_ja',
        'stage',
        'identity_type',
        'nationality',
        'admission_status',
        'is_required',
        'order',
    )

    fieldsets = (
        ('基本資料', {
            'fields': (
                'stage',
                'title',
                'description',
                'identity_type',
                'nationality',
                'admission_status',
                'official_url',
                'is_required',
                'order',
            )
        }),
        ('英文 English', {
            'fields': (
                'title_en',
                'description_en',
            )
        }),
        ('緬甸語 Burmese', {
            'fields': (
                'title_my',
                'description_my',
            )
        }),
        ('印尼語 Indonesian', {
            'fields': (
                'title_id',
                'description_id',
            )
        }),
        ('馬來語 Malay', {
            'fields': (
                'title_ms',
                'description_ms',
            )
        }),
        ('泰語 Thai', {
            'fields': (
                'title_th',
                'description_th',
            )
        }),
        ('日語 Japanese', {
            'fields': (
                'title_ja',
                'description_ja',
            )
        }),
    )

    list_filter = (
        'stage',
        'identity_type',
        'nationality',
        'admission_status',
        'is_required',
    )

    search_fields = (
        'title',
        'title_en',
        'title_my',
        'title_id',
        'title_ms',
        'title_th',
        'title_ja',
        'description',
    )

    ordering = ('stage__order', 'order')


@admin.register(StudentTask)
class StudentTaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'task',
        'status',
        'due_date',
        'completed_at',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'status',
        'task__stage',
        'due_date',
    )

    search_fields = (
        'student__user__name',
        'student__user__email',
        'task__title',
        'task__title_en',
        'task__title_my',
    )

    ordering = ('-created_at',)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'student_task',
        'is_read',
        'created_at',
    )

    list_filter = (
        'is_read',
        'created_at',
    )

    search_fields = (
        'student__user__name',
        'student__user__email',
        'message',
    )

    ordering = ('-created_at',)
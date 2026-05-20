from django.contrib import admin
from .models import FlowStage, Task, StudentTask, Reminder, Tip


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
        'name_ko',
        'name_vi',
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
        ('韓語 Korean', {
            'fields': (
                'name_ko',
                'description_ko',
            )
        }),
        ('越南語 Vietnamese', {
            'fields': (
                'name_vi',
                'description_vi',
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
        'name_ko',
        'name_vi',
    )

    ordering = ('order',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'task_code',
        'title_en',
        'title_my',
        'title_id',
        'title_ms',
        'title_th',
        'title_ja',
        'title_ko',
        'title_vi',
        'stage',
        'display_region',
        'display_identity_type',
        'display_nationality',
        'university',
        'admission_status',
        'deadline_type',
        'deadline_days',
        'is_required',
        'order',
    )

    fieldsets = (
        ('基本資料', {
            'fields': (
                'stage',
                'title',
                'task_code',
                'description',
                'region',
                'identity_type',
                'nationality',
                'university',
                'admission_status',
                'official_url',
                'required_documents',
                'apply_location',
                'apply_address',
                'apply_map_url',
                'is_required',
                'order',
            )
        }),
        ('期限設定', {
            'fields': (
                'deadline_type',
                'deadline_days',
                'deadline_text',
            ),
            'description': '「期限類型」選擇：無截止日期 / 只顯示文字說明 / 依抵台日期自動計算。若選擇「依抵台日期自動計算」，請填入「計算天數」。'
        }),
        ('英文 English', {
            'fields': (
                'title_en',
                'description_en',
                'required_documents_en',
                'apply_location_en',
                'deadline_text_en',
            )
        }),
        ('緬甸語 Burmese', {
            'fields': (
                'title_my',
                'description_my',
                'required_documents_my',
                'apply_location_my',
                'deadline_text_my',
            )
        }),
        ('印尼語 Indonesian', {
            'fields': (
                'title_id',
                'description_id',
                'required_documents_id',
                'apply_location_id',
                'deadline_text_id',
            )
        }),
        ('馬來語 Malay', {
            'fields': (
                'title_ms',
                'description_ms',
                'required_documents_ms',
                'apply_location_ms',
                'deadline_text_ms',
            )
        }),
        ('泰語 Thai', {
            'fields': (
                'title_th',
                'description_th',
                'required_documents_th',
                'apply_location_th',
                'deadline_text_th',
            )
        }),
        ('日語 Japanese', {
            'fields': (
                'title_ja',
                'description_ja',
                'required_documents_ja',
                'apply_location_ja',
                'deadline_text_ja',
            )
        }),
        ('韓語 Korean', {
            'fields': (
                'title_ko',
                'description_ko',
                'required_documents_ko',
                'apply_location_ko',
                'deadline_text_ko',
            )
        }),
        ('越南語 Vietnamese', {
            'fields': (
                'title_vi',
                'description_vi',
                'required_documents_vi',
                'apply_location_vi',
                'deadline_text_vi',
            )
        }),
    )

    list_filter = (
        'stage',
        'region',
        'identity_type',
        'nationality',
        'university',
        'admission_status',
        'deadline_type',
        'is_required',
    )

    search_fields = (
        'title',
        'task_code',
        'title_en',
        'title_my',
        'title_id',
        'title_ms',
        'title_th',
        'title_ja',
        'title_ko',
        'title_vi',
        'description',
    )

    ordering = ('stage__order', 'order')

    def display_region(self, obj):
        return obj.get_region_display() if obj.region else '-'
    display_region.short_description = '適用地區'

    def display_identity_type(self, obj):
        return obj.get_identity_type_display() if obj.identity_type else '-'
    display_identity_type.short_description = '適用身份類型'

    def display_nationality(self, obj):
        return obj.get_nationality_display() if obj.nationality else '-'
    display_nationality.short_description = '適用國籍'


@admin.register(StudentTask)
class StudentTaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'task',
        'status',
        'completed_at',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'status',
        'task__stage',
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


@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'title_en',
        'title_my',
        'title_id',
        'title_ms',
        'title_th',
        'title_ja',
        'title_ko',
        'title_vi',
        'official_url',
        'is_active',
        'order',
    )

    fieldsets = (
        ('基本資料', {
            'fields': (
                'title',
                'content',
                'official_url',
                'is_active',
                'order',
            )
        }),
        ('英文 English', {
            'classes': ('collapse',),
            'fields': (
                'title_en',
                'content_en',
            )
        }),
        ('緬甸語 Burmese', {
            'classes': ('collapse',),
            'fields': (
                'title_my',
                'content_my',
            )
        }),
        ('印尼語 Indonesian', {
            'classes': ('collapse',),
            'fields': (
                'title_id',
                'content_id',
            )
        }),
        ('馬來語 Malay', {
            'classes': ('collapse',),
            'fields': (
                'title_ms',
                'content_ms',
            )
        }),
        ('泰語 Thai', {
            'classes': ('collapse',),
            'fields': (
                'title_th',
                'content_th',
            )
        }),
        ('日語 Japanese', {
            'classes': ('collapse',),
            'fields': (
                'title_ja',
                'content_ja',
            )
        }),
        ('韓語 Korean', {
            'classes': ('collapse',),
            'fields': (
                'title_ko',
                'content_ko',
            )
        }),
        ('越南語 Vietnamese', {
            'classes': ('collapse',),
            'fields': (
                'title_vi',
                'content_vi',
            )
        }),
    )

    list_filter = ('is_active',)
    search_fields = ('title', 'title_en', 'content')
    ordering = ('order',)
from django.contrib import admin
from .models import FlowStage, Task, StudentTask, Reminder, Tip, TipLink, TipLinkCategory


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
        'is_pre_arrival',
    )

    fieldsets = (
        ('基本資料', {
            'fields': (
                'name',
                'description',
                'order',
                'is_pre_arrival',
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
        'stage',
        'display_region',
        'display_identity_type',
        'display_nationality',
        'university',
        'admission_status',
        'require_taiwan_id',
        'require_deferred',
        # 'require_indo_prep',
        'deadline_type',
        'deadline_days',
        'deadline_date',
        'deadline_text',
        'is_required',
        'order',
    )

    list_editable = (
        'deadline_type',
        'deadline_days',
        'deadline_date',
        'deadline_text',
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
        ('進階個人化條件 (對應註冊問答)', {
            'fields': (
                'require_taiwan_id',
                'require_deferred',
                # 'require_indo_prep',
            ),
            'description': '這些條件對應模塊一註冊時的問答。留空=不限制，是=僅回答「是」的學生可見，否=僅回答「否」的學生可見。'
        }),
        ('期限設定', {
            'fields': (
                'deadline_type',
                'deadline_days',
                'deadline_date',
                'deadline_text',
            ),
            'description': '「期限類型」選擇：無截止日期 / 只顯示文字說明 / 依抵台日期自動計算 / 固定截止日期。若選擇「依抵台日期自動計算」，請填入「計算天數（正數為抵台後，負數為抵台前）」；若選擇「固定截止日期」，請填入「固定截止日期」。'
        }),
        ('英文 English', {
            'fields': (
                'title_en',
                'description_en',
                'required_documents_en',
                'apply_location_en',
                'apply_address_en',
                'deadline_text_en',
            )
        }),
        ('緬甸語 Burmese', {
            'fields': (
                'title_my',
                'description_my',
                'required_documents_my',
                'apply_location_my',
                'apply_address_my',
                'deadline_text_my',
            )
        }),
        ('印尼語 Indonesian', {
            'fields': (
                'title_id',
                'description_id',
                'required_documents_id',
                'apply_location_id',
                'apply_address_id',
                'deadline_text_id',
            )
        }),
        ('馬來語 Malay', {
            'fields': (
                'title_ms',
                'description_ms',
                'required_documents_ms',
                'apply_location_ms',
                'apply_address_ms',
                'deadline_text_ms',
            )
        }),
        ('泰語 Thai', {
            'fields': (
                'title_th',
                'description_th',
                'required_documents_th',
                'apply_location_th',
                'apply_address_th',
                'deadline_text_th',
            )
        }),
        ('日語 Japanese', {
            'fields': (
                'title_ja',
                'description_ja',
                'required_documents_ja',
                'apply_location_ja',
                'apply_address_ja',
                'deadline_text_ja',
            )
        }),
        ('韓語 Korean', {
            'fields': (
                'title_ko',
                'description_ko',
                'required_documents_ko',
                'apply_location_ko',
                'apply_address_ko',
                'deadline_text_ko',
            )
        }),
        ('越南語 Vietnamese', {
            'fields': (
                'title_vi',
                'description_vi',
                'required_documents_vi',
                'apply_location_vi',
                'apply_address_vi',
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
        'require_taiwan_id',
        'require_deferred',
        # 'require_indo_prep',
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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'deadline_date':
            from django import forms
            kwargs['widget'] = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
        return super().formfield_for_dbfield(db_field, request, **kwargs)


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


@admin.register(TipLinkCategory)
class TipLinkCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_en', 'icon')
    search_fields = ('name', 'name_en')

class TipLinkInline(admin.StackedInline):
    model = TipLink
    extra = 1
    fields = (
        'url',
        'link_category',
        ('label', 'label_en', 'label_my', 'label_id', 'label_ms',
         'label_th', 'label_ja', 'label_ko', 'label_vi')
    )
    verbose_name = "小貼士鏈結"
    verbose_name_plural = "小貼士鏈結"

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
        'display_identity_type',
        'is_active',
        'order',
    )

    def display_identity_type(self, obj):
        return obj.get_identity_type_display() if obj.identity_type else '-'
    display_identity_type.short_description = '適用身份類型'

    fieldsets = (
        ('基本資料', {
            'fields': (
                'title',
                'content',
                'identity_type',
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

    inlines = [TipLinkInline]
    list_filter = ('is_active',)
    search_fields = ('title', 'title_en', 'content')
    ordering = ('order',)
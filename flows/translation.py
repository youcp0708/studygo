from modeltranslation.translator import register, TranslationOptions
from flows.models import FlowStage, Task, Reminder

@register(FlowStage)
class FlowStageTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

@register(Task)
class TaskTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

@register(Reminder)
class ReminderTranslationOptions(TranslationOptions):
    fields = ('message',)

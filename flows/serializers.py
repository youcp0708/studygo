"""
flows/serializers.py
負責 flows 應用程式的資料序列化與反序列化 (Model <-> JSON)

注意：一律使用明確的 fields 清單，不用 fields='__all__'，
避免把內部分流條件（require_taiwan_id 等）與所有多語原始欄位
整包傳給前端（前端顯示用的多語文字已由 view 的 localized 欄位提供）。
"""
from rest_framework import serializers
from .models import FlowStage, Task, StudentTask, Reminder, Tip, TipLink

# Task 任務資料轉成 JSON 格式(前後端分離)
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id', 'stage', 'title', 'description',
            'official_url', 'required_documents',
            'apply_location', 'apply_address', 'apply_map_url',
            'deadline_type', 'deadline_days', 'deadline_date', 'deadline_text',
            'is_required', 'order',
        )

# 給 StudentTask 内嵌用的精簡版 Task（前端顯示只需要這些）
class TaskLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'stage', 'title', 'is_required', 'order')

# FlowStage 流程階段資料轉成 JSON 格式(前後端分離)，回傳流程階段時，也把這個階段底下的任務一起回傳。
class FlowStageSerializer(serializers.ModelSerializer):
    # 這裡的 'tasks' 對應 models.py 中 Task 的 related_name="tasks"
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = FlowStage
        fields = ('id', 'name', 'description', 'order', 'is_pre_arrival', 'tasks')



# StudentTask 學生任務進度資料轉成 JSON 格式，回傳「某個學生自己的任務進度」
class StudentTaskSerializer(serializers.ModelSerializer):
    # 為了讓前端方便顯示，把關聯的 Task 精簡資料也附加上去
    task_detail = TaskLiteSerializer(source='task', read_only=True)

    # 把 status 的中文顯示值拉出來 (例如 'in_progress' -> '進行中')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StudentTask
        fields = (
            'id', 'student', 'task', 'task_detail',
            'status', 'status_display', 'note',
            'completed_at', 'created_at', 'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class ReminderSerializer(serializers.ModelSerializer):
    # 依目前瀏覽頁面的語言即時翻譯提醒內容（見 Reminder.get_message）
    message = serializers.SerializerMethodField()
    # 點擊這則提醒要導去的 StudentTask id（見 Reminder.get_link_task_id）
    link_task_id = serializers.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = ('id', 'student_task', 'link_task_id', 'message', 'is_read', 'created_at')

    def get_message(self, obj):
        return obj.get_message()

    def get_link_task_id(self, obj):
        return obj.get_link_task_id()


class TipLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipLink
        fields = ("id", "url", "label")


class TipSerializer(serializers.ModelSerializer):
    links = TipLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Tip
        fields = ("id", "title", "content", "is_active", "order", "links")

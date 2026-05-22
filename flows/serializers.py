"""
flows/serializers.py
負責 flows 應用程式的資料序列化與反序列化 (Model <-> JSON)
"""
from rest_framework import serializers
from .models import FlowStage, Task, StudentTask, Reminder, Tip, TipLink

# Task 任務資料轉成 JSON 格式(前後端分離)
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

# FlowStage 流程階段資料轉成 JSON 格式(前後端分離)，回傳流程階段時，也把這個階段底下的任務一起回傳。
class FlowStageSerializer(serializers.ModelSerializer):
    # 這裡的 'tasks' 對應 models.py 中 Task 的 related_name="tasks"
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = FlowStage
        fields = '__all__'



# StudentTask 學生任務進度資料轉成 JSON 格式，回傳「某個學生自己的任務進度」
class StudentTaskSerializer(serializers.ModelSerializer):
    # 為了讓前端方便顯示，把關聯的 Task 詳細資料也附加上去
    task_detail = TaskSerializer(source='task', read_only=True)

    # 把 status 的中文顯示值拉出來 (例如 'in_progress' -> '進行中')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StudentTask
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = '__all__'


class TipLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipLink
        fields = ("id", "url", "label")


class TipSerializer(serializers.ModelSerializer):
    links = TipLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Tip
        fields = ("id", "title", "content", "is_active", "order", "links")

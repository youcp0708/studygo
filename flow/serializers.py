"""
flow/serializers.py
"""

from rest_framework import serializers
from .models import FlowStepTemplate, ProcessFlow, UserTask


class UserTaskSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display   = serializers.CharField(source='get_status_display',   read_only=True)
    is_overdue       = serializers.BooleanField(read_only=True)

    class Meta:
        model  = UserTask
        fields = [
            'id', 'title', 'description',
            'category', 'category_display',
            'status', 'status_display',
            'is_required', 'order',
            'due_date', 'completed_at', 'is_overdue',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class ProcessFlowSerializer(serializers.ModelSerializer):
    tasks           = UserTaskSerializer(many=True, read_only=True)
    completion_rate = serializers.IntegerField(read_only=True)
    pending_count   = serializers.IntegerField(read_only=True)
    overdue_count   = serializers.IntegerField(read_only=True)

    class Meta:
        model  = ProcessFlow
        fields = [
            'id', 'identity_type', 'admission_status',
            'completion_rate', 'pending_count', 'overdue_count',
            'created_at', 'updated_at', 'tasks',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UpdateTaskSerializer(serializers.Serializer):
    status   = serializers.ChoiceField(
        choices=['todo', 'in_progress', 'done'], required=False
    )
    notes    = serializers.CharField(required=False, allow_blank=True)
    due_date = serializers.DateField(required=False, allow_null=True)

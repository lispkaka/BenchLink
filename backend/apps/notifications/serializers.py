from rest_framework import serializers
from .models import NotificationChannel
from apps.projects.serializers import ProjectSerializer


class NotificationChannelSerializer(serializers.ModelSerializer):
    """通知渠道序列化器"""
    project_detail = ProjectSerializer(source='project', read_only=True)
    channel_type_display = serializers.CharField(source='get_channel_type_display', read_only=True)
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'channel_type_display',
            'webhook_url', 'secret', 'is_active',
            'project', 'project_detail',
            'notify_on_success', 'notify_on_failure', 'notify_on_complete',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret': {'write_only': True}  # 密钥只写不读
        }




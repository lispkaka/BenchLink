"""
通知服务
"""
from django.db.models import Q
from .models import NotificationChannel
from .notifiers import get_notifier


def send_execution_notification(execution):
    """
    发送执行通知
    根据执行状态和通知规则，发送到配置的渠道
    """
    # 获取该项目或全局的通知渠道
    channels = NotificationChannel.objects.filter(
        is_active=True
    ).filter(
        Q(project=execution.project) | Q(project__isnull=True)
    )
    
    sent_count = 0
    errors = []
    
    for channel in channels:
        # 根据通知规则判断是否需要发送
        should_send = False
        
        if execution.status == 'passed' and channel.notify_on_success:
            should_send = True
        elif execution.status == 'failed' and channel.notify_on_failure:
            should_send = True
        elif channel.notify_on_complete:
            should_send = True
        
        if not should_send:
            continue
        
        # 获取通知器并发送
        notifier = get_notifier(channel.channel_type)
        if notifier:
            success, message = notifier.send(execution, channel)
            if success:
                sent_count += 1
            else:
                errors.append(f'{channel.name}: {message}')
    
    return sent_count, errors


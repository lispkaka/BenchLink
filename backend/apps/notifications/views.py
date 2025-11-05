from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import NotificationChannel
from .serializers import NotificationChannelSerializer
from .notifiers import get_notifier


class NotificationChannelViewSet(viewsets.ModelViewSet):
    """通知渠道视图集"""
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取通知渠道列表，支持按项目筛选"""
        project_id = self.request.query_params.get('project_id')
        queryset = NotificationChannel.objects.all()
        
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """测试通知渠道"""
        channel = self.get_object()
        
        # 创建测试消息
        class TestExecution:
            """测试执行对象"""
            def __init__(self):
                self.status = 'passed'
                self.project = type('obj', (object,), {'name': '测试项目'})()
                self.testsuite = type('obj', (object,), {'name': '测试套件'})()
                self.testcase = None
                self.executor = type('obj', (object,), {'username': '测试用户'})()
                self.result = {'total': 5, 'passed': 5, 'failed': 0, 'pass_rate': 100}
                self.start_time = None
                self.duration = 1.23
                self.id = 999
            
            def get_status_display(self):
                return '通过'
        
        test_execution = TestExecution()
        
        # 发送测试消息
        notifier = get_notifier(channel.channel_type)
        if not notifier:
            return Response({
                'error': f'不支持的通知类型: {channel.channel_type}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success, message = notifier.send(test_execution, channel)
        
        if success:
            return Response({
                'message': '测试消息发送成功',
                'detail': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': '测试消息发送失败',
                'detail': message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

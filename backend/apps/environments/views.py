from rest_framework import viewsets
from .models import Environment, GlobalToken
from .serializers import EnvironmentSerializer, GlobalTokenSerializer


class EnvironmentViewSet(viewsets.ModelViewSet):
    """环境视图集"""
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return Environment.objects.filter(project_id=project_id)
        return Environment.objects.all()


class GlobalTokenViewSet(viewsets.ModelViewSet):
    """全局 Token 视图集"""
    queryset = GlobalToken.objects.all()
    serializer_class = GlobalTokenSerializer
    
    def get_queryset(self):
        # 支持按启用状态筛选
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            return GlobalToken.objects.filter(is_active=is_active.lower() == 'true')
        return GlobalToken.objects.all()




from django.db import models
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """项目视图集"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()
        
        # 支持按项目名称搜索
        name = self.request.query_params.get('name', '')
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取项目统计信息"""
        # 获取筛选条件
        name = request.query_params.get('name', '')
        
        # 获取基础查询集
        queryset = self.get_queryset()
        
        # 统计总数
        total = queryset.count()
        active = queryset.filter(is_active=True).count()
        
        # 统计各项目的接口、用例、套件数量
        projects_with_stats = queryset.annotate(
            api_count=Count('apis', distinct=True),
            testcase_count=Count('testcases', distinct=True),
            testsuite_count=Count('testsuites', distinct=True),
            environment_count=Count('environments', distinct=True)
        )
        
        # 计算总数
        total_apis = sum(p.api_count for p in projects_with_stats)
        total_cases = sum(p.testcase_count for p in projects_with_stats)
        total_suites = sum(p.testsuite_count for p in projects_with_stats)
        total_environments = sum(p.environment_count for p in projects_with_stats)
        
        return Response({
            'total': total,
            'active': active,
            'total_apis': total_apis,
            'total_cases': total_cases,
            'total_suites': total_suites,
            'total_environments': total_environments,
            'projects': [
                {
                    'id': p.id,
                    'name': p.name,
                    'api_count': p.api_count,
                    'testcase_count': p.testcase_count,
                    'testsuite_count': p.testsuite_count,
                    'environment_count': p.environment_count
                }
                for p in projects_with_stats
            ]
        })


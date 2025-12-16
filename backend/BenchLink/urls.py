"""
URL configuration for BenchLink project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def api_root(request):
    """API 根路径，返回可用的 API 端点"""
    return JsonResponse({
        'message': 'BenchLink API Server',
        'version': '1.0',
        'endpoints': {
            'admin': '/admin/',
            'users': '/api/users/',
            'projects': '/api/projects/',
            'environments': '/api/environments/',
            'apis': '/api/apis/',
            'testcases': '/api/testcases/',
            'testsuites': '/api/testsuites/',
            'executions': '/api/executions/',
            'scheduler': '/api/scheduler/',
            'notifications': '/api/notifications/',
        },
        'frontend': 'http://localhost:5173'
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/environments/', include('apps.environments.urls')),
    path('api/apis/', include('apps.apis.urls')),
    path('api/testcases/', include('apps.testcases.urls')),
    path('api/testsuites/', include('apps.testsuites.urls')),
    path('api/executions/', include('apps.executions.urls')),
    path('api/scheduler/', include('apps.scheduler.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    # OpenAPI schema & Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# 静态文件和媒体文件配置
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # 生产环境也需要静态文件支持
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()




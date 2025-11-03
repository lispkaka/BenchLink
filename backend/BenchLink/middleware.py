"""
自定义中间件
"""
from django.utils.deprecation import MiddlewareMixin


class DisableCSRFForAPI(MiddlewareMixin):
    """
    为API路径禁用CSRF检查
    """
    def process_request(self, request):
        # 如果路径以/api/开头，禁用CSRF检查
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None



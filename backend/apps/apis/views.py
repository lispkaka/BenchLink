from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import requests
import re
import time
from typing import Dict, Any, Optional
from .models import API
from .serializers import APISerializer


class APIViewSet(viewsets.ModelViewSet):
    """接口视图集"""
    queryset = API.objects.all()
    serializer_class = APISerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return API.objects.filter(project_id=project_id)
        return API.objects.all()

    def _replace_variables(self, text: str, variables: Dict = None) -> str:
        """替换变量 ${variable}"""
        if not text or not isinstance(text, str):
            return text
        
        vars_dict = variables or {}
        
        def replace_match(match):
            var_name = match.group(1)
            return str(vars_dict.get(var_name, match.group(0)))
        
        return re.sub(r'\$\{(\w+)\}', replace_match, text)
    
    def _replace_variables_in_dict(self, data: Dict, variables: Dict = None) -> Dict:
        """递归替换字典中的变量"""
        if isinstance(data, dict):
            return {k: self._replace_variables_in_dict(v, variables) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables_in_dict(item, variables) for item in data]
        elif isinstance(data, str):
            return self._replace_variables(data, variables)
        else:
            return data

    def _build_url(self, api_instance: API, base_url: str = '') -> str:
        """构建完整的请求URL（不替换变量，变量在execute中替换）"""
        api_url = api_instance.url.strip()
        
        # 如果已经是完整URL，直接返回
        if api_url.startswith(('http://', 'https://')):
            return api_url
        
        # 如果有base_url，拼接
        if base_url:
            base_url = base_url.rstrip('/')
            api_url = api_url.lstrip('/')
            return f"{base_url}/{api_url}" if api_url else base_url
        
        # 如果没有base_url，尝试从接口关联的项目中获取环境
        if api_instance.project:
            from apps.environments.models import Environment
            # 获取项目的第一个激活的环境
            env = Environment.objects.filter(
                project=api_instance.project,
                is_active=True
            ).first()
            if env and env.base_url:
                base_url = env.base_url.rstrip('/')
                api_url = api_url.lstrip('/')
                return f"{base_url}/{api_url}" if api_url else base_url
        
        # 如果都没有，抛出错误
        raise ValueError(
            f"无法构建完整URL：接口URL是相对路径 '{api_url}'，但未提供base_url。"
            f"请选择以下方式之一：1) 在接口URL中填写完整地址（如：https://api.example.com/point/pointRecord/list）；"
            f"2) 在项目的环境配置中创建并激活环境，填写base_url；"
            f"3) 执行接口时提供base_url参数。"
        )

    def _build_headers(self, api_instance: API, variables: Dict = None) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if api_instance.headers:
            headers.update(api_instance.headers)
        
        # 替换变量
        headers = {k: self._replace_variables(str(v), variables) for k, v in headers.items()}
        
        return headers

    def _build_auth(self, api_instance: API, variables: Dict = None) -> Optional[Any]:
        """构建认证信息"""
        if not api_instance.auth_type:
            return None
        
        auth_config = api_instance.auth_config or {}
        
        if api_instance.auth_type.lower() == 'bearer' or api_instance.auth_type.lower() == 'token':
            token = self._replace_variables(auth_config.get('token', ''), variables)
            return ('Bearer', token) if token else None
        elif api_instance.auth_type.lower() == 'basic':
            username = self._replace_variables(auth_config.get('username', ''), variables)
            password = self._replace_variables(auth_config.get('password', ''), variables)
            if username and password:
                return (username, password)
        
        return None

    def _execute_single_request(self, api_instance: API, variables: Dict = None, base_url: str = '') -> Dict[str, Any]:
        """执行单次请求（用于参数化和普通执行）"""
        try:
            # 构建请求参数
            url = self._build_url(api_instance, base_url)
            headers = self._build_headers(api_instance, variables)
            params = self._replace_variables_in_dict(api_instance.params or {}, variables)
            body = self._replace_variables_in_dict(api_instance.body or {}, variables)
            auth = self._build_auth(api_instance, variables)
            
            # 替换URL中的变量
            url = self._replace_variables(url, variables)
            
            # 准备请求数据
            request_kwargs = {
                'method': api_instance.method,
                'url': url,
                'headers': headers,
                'params': params,
                'timeout': 30
            }
            
            # 添加认证
            if auth:
                if isinstance(auth, tuple) and len(auth) == 2:
                    if auth[0] == 'Bearer':
                        headers['Authorization'] = f'Bearer {auth[1]}'
                    else:
                        request_kwargs['auth'] = auth
            
            # 添加请求体
            if api_instance.method in ['POST', 'PUT', 'PATCH']:
                if body:
                    request_kwargs['json'] = body
            
            # 发送请求（只计算HTTP请求的实际时间）
            # 使用Session来复用连接，减少连接建立时间
            from apps.testcases.executor import get_session
            session = get_session()
            method = request_kwargs.pop('method')
            response = session.request(method=method, **request_kwargs)
            
            # 使用response.elapsed获取真实的HTTP请求时间（不包括平台处理时间）
            http_request_time_ms = response.elapsed.total_seconds() * 1000  # 转换为毫秒
            
            # 构建响应
            result = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'time': round(http_request_time_ms, 2),
                'url': url,
                'success': 200 <= response.status_code < 300,
                'variables': variables.copy() if variables else {}  # 记录使用的变量
            }
            
            # 尝试解析JSON响应
            try:
                result['json'] = response.json()
            except:
                pass
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                'error': '请求超时',
                'time': 30000,
                'success': False,
                'variables': variables.copy() if variables else {}
            }
        except requests.exceptions.ConnectionError:
            return {
                'error': '连接错误，请检查URL是否正确',
                'time': 0,
                'success': False,
                'variables': variables.copy() if variables else {}
            }
        except Exception as e:
            return {
                'error': str(e),
                'time': 0,
                'success': False,
                'variables': variables.copy() if variables else {}
            }

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行接口请求（支持参数化）"""
        api_instance = self.get_object()
        
        # 获取请求参数
        data = request.data
        variables = data.get('variables', {})
        base_url = data.get('base_url', '')
        
        # 检查参数化模式
        parameterized_mode = data.get('parameterized_mode')
        if parameterized_mode is None:
            # 如果前端未指定，使用API定义的参数化模式
            parameterized_mode = api_instance.parameterized_mode
        
        # 获取参数化数据（优先级：前端传入 > API定义）
        parameterized_data = data.get('parameterized_data') or api_instance.parameterized_data
        
        # 如果启用参数化且有参数化数据
        if parameterized_mode == 'enabled' and parameterized_data and isinstance(parameterized_data, list) and len(parameterized_data) > 0:
            # 参数化执行：循环执行多次
            results = []
            for idx, param_set in enumerate(parameterized_data):
                # 合并变量：基础变量 + 参数化数据
                merged_vars = {**variables, **param_set}
                result = self._execute_single_request(api_instance, merged_vars, base_url)
                result['index'] = idx + 1  # 记录执行序号
                results.append(result)
            
            # 统计结果
            passed_count = sum(1 for r in results if r.get('success', False))
            failed_count = len(results) - passed_count
            total_time = sum(r.get('time', 0) for r in results)
            
            return Response({
                'parameterized': True,
                'total': len(results),
                'passed': passed_count,
                'failed': failed_count,
                'total_time': round(total_time, 2),
                'results': results
            }, status=status.HTTP_200_OK)
        else:
            # 普通执行：单次
            result = self._execute_single_request(api_instance, variables, base_url)
            return Response(result, status=status.HTTP_200_OK)




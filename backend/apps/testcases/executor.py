"""
测试用例执行引擎
"""
import requests
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
from django.utils import timezone
from apps.environments.models import GlobalToken

# 禁用SSL警告（开发环境）
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建全局Session用于连接复用（减少连接建立时间）
_global_session = None

def get_session():
    """获取全局Session实例（连接复用）"""
    global _global_session
    if _global_session is None:
        _global_session = requests.Session()
        # 配置重试策略
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        retry_strategy = Retry(
            total=0,  # 不重试，避免影响时间统计
            backoff_factor=0,
            status_forcelist=[]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        _global_session.mount("http://", adapter)
        _global_session.mount("https://", adapter)
    return _global_session


class TestCaseExecutor:
    """测试用例执行器"""
    
    def __init__(self, testcase, environment=None):
        """
        初始化执行器
        :param testcase: TestCase 实例
        :param environment: Environment 实例（可选）
        """
        self.testcase = testcase
        self.api = testcase.api
        self.environment = environment or testcase.environment
        self.variables = {}
        
        # 【修复】立即注入全局Token的variables和token值，无论接口是否配置认证
        # 这样单独执行测试用例时，${token}等变量可以从全局Token获取
        global_token = self._get_global_token()
        if global_token:
            # 1. 注入全局Token的variables字段（如果有配置）
            if global_token.variables:
                self.variables.update(global_token.variables)
            # 2. 【关键】将token值自动注入为 "_global_token_static" 变量（保留全局Token的静态值）
            # 注意：不直接注入到"token"，避免覆盖测试套件中动态提取的token
            if global_token.token:
                self.variables['_global_token_static'] = global_token.token
        
        self.response = None
        self.execution_result = {
            'status_code': None,
            'headers': {},
            'body': None,
            'time': 0,
            'success': False,
            'assertions': [],
            'error': None
        }
    
    def _replace_variables(self, text: str) -> str:
        """替换变量 ${variable}"""
        if not text or not isinstance(text, str):
            return text
        
        # 合并环境变量和测试用例变量
        all_vars = {}
        if self.environment:
            all_vars.update(self.environment.variables or {})
        all_vars.update(self.testcase.variables or {})
        all_vars.update(self.variables or {})
        
        # 替换 ${variable} 格式的变量
        def replace_match(match):
            var_name = match.group(1)
            return str(all_vars.get(var_name, match.group(0)))
        
        return re.sub(r'\$\{(\w+)\}', replace_match, text)
    
    def _replace_variables_in_dict(self, data: Dict) -> Dict:
        """递归替换字典中的变量"""
        if isinstance(data, dict):
            return {k: self._replace_variables_in_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables_in_dict(item) for item in data]
        elif isinstance(data, str):
            return self._replace_variables(data)
        else:
            return data
    
    def _build_url(self) -> str:
        """构建完整的请求URL（支持用例级别的URL覆盖）"""
        # 方案A：优先级：用例覆盖 > 接口定义
        if self.testcase.url_override:
            api_url = self.testcase.url_override.strip()
        else:
            api_url = self.api.url.strip()
        
        # 替换变量
        api_url = self._replace_variables(api_url)
        
        # 如果API URL已经是完整URL（以http://或https://开头），直接使用
        if api_url.startswith(('http://', 'https://')):
            return api_url
        
        # 否则，拼接环境的基础URL
        if self.environment and self.environment.base_url:
            base_url = self.environment.base_url.rstrip('/')
            api_url = api_url.lstrip('/')
            return f"{base_url}/{api_url}" if api_url else base_url
        
        # 如果没有环境配置，使用API URL（可能是相对路径）
        return api_url
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头（支持用例级别的请求头覆盖）"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 合并环境默认请求头
        if self.environment and self.environment.headers:
            headers.update(self.environment.headers)
        
        # 先合并接口定义的请求头
        if self.api.headers:
            headers.update(self.api.headers)
        
        # 再合并用例覆盖的请求头（会覆盖同名字段）
        if self.testcase.headers_override:
            headers.update(self.testcase.headers_override)
        
        # 替换变量
        headers = {k: self._replace_variables(str(v)) for k, v in headers.items()}
        
        return headers
    
    def _get_global_token(self) -> Optional[GlobalToken]:
        """
        获取全局 Token
        优先级：默认 Token > 启用的第一个 Token
        """
        try:
            # 优先获取默认 Token
            default_token = GlobalToken.objects.filter(is_active=True, is_default=True).first()
            if default_token:
                return default_token
            
            # 如果没有默认 Token，获取第一个启用的 Token
            active_token = GlobalToken.objects.filter(is_active=True).first()
            return active_token
        except Exception:
            return None
    
    def _build_auth(self) -> Optional[Any]:
        """
        构建认证信息
        支持多种认证方式：
        1. Bearer Token: auth_type='bearer' 或 'token', auth_config={'token': 'xxx'} 或 {'token': '${token_var}'}
        2. Django REST Framework Token: auth_type='drf_token', auth_config={'token': 'xxx'} 或 {'token': '${token_var}'}
        3. Basic Auth: auth_type='basic', auth_config={'username': 'xxx', 'password': 'xxx'}
        4. 自定义 Header Token: auth_type='header', auth_config={'header_name': 'Authorization', 'token': 'xxx'}
        
        如果接口未配置认证，且启用了全局 Token，则自动使用全局 Token
        """
        # 如果接口配置了认证类型，使用接口配置
        if self.api.auth_type:
            auth_config = self.api.auth_config or {}
            auth_type_lower = self.api.auth_type.lower()
            
            if auth_type_lower in ['bearer', 'token']:
                # Bearer Token 认证: Authorization: Bearer <token>
                token = auth_config.get('token', '')
                if not token:
                    # 尝试从变量中获取 token
                    token = self.variables.get('token') or self.variables.get('access_token')
                if token:
                    token = self._replace_variables(str(token))
                    return ('Bearer', token) if token else None
            
            elif auth_type_lower == 'drf_token':
                # Django REST Framework Token 认证: Authorization: Token <token>
                token = auth_config.get('token', '')
                if not token:
                    # 尝试从变量中获取 token
                    token = self.variables.get('token') or self.variables.get('access_token')
                if token:
                    token = self._replace_variables(str(token))
                    return ('Token', token) if token else None
            
            elif auth_type_lower == 'basic':
                # Basic 认证
                username = auth_config.get('username', '')
                password = auth_config.get('password', '')
                if not username:
                    username = self.variables.get('username') or self.variables.get('basic_username')
                if not password:
                    password = self.variables.get('password') or self.variables.get('basic_password')
                
                if username:
                    username = self._replace_variables(str(username))
                if password:
                    password = self._replace_variables(str(password))
                
                if username and password:
                    return (username, password)
            
            elif auth_type_lower == 'header':
                # 自定义 Header Token: 直接在 headers 中添加，不在 auth 中处理
                # 这种方式会在 _build_headers 中处理
                return None
        
        # 如果接口未配置认证，尝试使用Token（优先级：动态Token > 全局Token）
        # 注意：全局Token的variables已在__init__中注入，这里只处理认证
        
        # 【优化】优先使用动态Token（从测试套件中前置用例提取的）
        # 判断依据：如果variables中有'token'且不是全局Token的静态值，则认为是动态Token
        dynamic_token = self.variables.get('token')
        global_token_static = self.variables.get('_global_token_static')
        
        # 如果有动态Token（且与全局Token静态值不同），优先使用动态Token
        if dynamic_token and dynamic_token != global_token_static:
            # 使用动态Token（从测试套件中提取的）
            token_value = self._replace_variables(str(dynamic_token))
            # 默认使用Bearer类型（如果有全局Token配置，使用其类型）
            global_token = self._get_global_token()
            if global_token:
                if global_token.auth_type == 'bearer':
                    return ('Bearer', token_value)
                elif global_token.auth_type == 'drf_token':
                    return ('Token', token_value)
                elif global_token.auth_type == 'header':
                    # Header 类型在 _build_headers 中处理
                    return None
            else:
                # 没有全局Token配置，默认使用Bearer
                return ('Bearer', token_value)
        
        # 如果没有动态Token，使用全局Token的静态值
        global_token = self._get_global_token()
        if global_token:
            token_value = global_token.token
            # 替换 Token 中的变量
            token_value = self._replace_variables(token_value)
            
            if global_token.auth_type == 'bearer':
                return ('Bearer', token_value)
            elif global_token.auth_type == 'drf_token':
                return ('Token', token_value)
            elif global_token.auth_type == 'header':
                # Header 类型在 _build_headers 中处理
                return None
        
        return None
    
    def _extract_variables(self) -> None:
        """从响应中提取变量到self.variables"""
        if not self.response:
            return
        
        # 从testcase.variables中获取extractors配置
        extractors_config = self.testcase.variables.get('extractors', {})
        if not extractors_config:
            return
        
        # 尝试解析JSON响应
        response_json = None
        try:
            response_json = self.response.json()
        except:
            response_json = None
        
        # 遍历extractors配置，提取变量
        for var_name, json_path in extractors_config.items():
            try:
                if json_path.startswith('$.'):
                    # JSON路径提取（去掉$.前缀）
                    if response_json:
                        value = self._get_json_value(json_path[2:])  # 去掉$.前缀
                        if value is not None:
                            self.variables[var_name] = value
                elif json_path.startswith('$[') or (json_path.startswith('[') and isinstance(response_json, list)):
                    # JSON路径数组提取（简化处理）
                    if response_json:
                        # 简化处理：去掉$前缀，尝试解析
                        clean_path = json_path[1:] if json_path.startswith('$') else json_path
                        # 尝试简单解析数组路径（如[0].id或0.id）
                        try:
                            # 去掉开头的[和]
                            path_parts = clean_path.replace('[', '').replace(']', '.').strip('.').split('.')
                            value = response_json
                            for part in path_parts:
                                if part:
                                    if isinstance(value, list):
                                        value = value[int(part)] if part.isdigit() and int(part) < len(value) else None
                                    elif isinstance(value, dict):
                                        value = value.get(part)
                                    else:
                                        value = None
                                    if value is None:
                                        break
                            if value is not None:
                                self.variables[var_name] = value
                        except (ValueError, IndexError, TypeError):
                            pass
                elif json_path.startswith('header.'):
                    # 从响应头提取
                    header_name = json_path[7:]  # 去掉header.前缀
                    if header_name in self.response.headers:
                        self.variables[var_name] = self.response.headers[header_name]
                elif json_path == 'status_code':
                    # 提取状态码
                    self.variables[var_name] = self.response.status_code
                elif json_path == 'body':
                    # 提取整个响应体
                    self.variables[var_name] = self._get_response_text()
                else:
                    # 尝试直接作为JSON路径
                    if response_json:
                        value = self._get_json_value(json_path)
                        if value is not None:
                            self.variables[var_name] = value
            except Exception as e:
                # 提取失败，记录但不影响执行
                print(f"变量提取失败 {var_name}: {str(e)}")
    
    def _validate_script(self, script: str) -> bool:
        """验证脚本是否安全"""
        import ast
        # 禁止的危险操作
        FORBIDDEN_NODES = (
            ast.Import, ast.ImportFrom,  # 禁止导入
        )
        FORBIDDEN_FUNCTIONS = {
            'open', 'file', '__import__', 'exec', 'eval', 'compile',
            'reload', 'input', 'raw_input', 'execfile', 'exit', 'quit',
        }
        
        try:
            tree = ast.parse(script)
            for node in ast.walk(tree):
                # 检查禁止的节点类型
                if isinstance(node, FORBIDDEN_NODES):
                    return False
                # 检查禁止的函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in FORBIDDEN_FUNCTIONS:
                            return False
                    # 检查属性访问（如 __import__）
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in FORBIDDEN_FUNCTIONS:
                            return False
            return True
        except SyntaxError:
            return False
        except Exception:
            # 如果解析失败，拒绝执行
            return False
    
    def _execute_pre_script(self) -> None:
        """执行前置脚本（Python脚本）"""
        if not self.testcase.pre_script:
            return
        
        script = self.testcase.pre_script
        
        # 验证脚本安全性
        if not self._validate_script(script):
            print(f"前置脚本包含不安全操作，已拒绝执行")
            return
        
        # 限制脚本长度，防止资源耗尽
        if len(script) > 10000:  # 10KB限制
            print(f"前置脚本过长（{len(script)}字符），已拒绝执行")
            return
        
        # 准备脚本执行上下文
        context = {
            'variables': self.variables,
            'testcase': self.testcase,
            'api': self.api,
            'environment': self.environment,
            # 提供一些常用函数
            'set_variable': lambda name, value: self.variables.update({name: value}),
            'get_variable': lambda name: self.variables.get(name),
            'print': print,
        }
        
        try:
            # 执行脚本（注意：生产环境应该使用更安全的方式）
            # 限制内置函数，只允许安全操作
            safe_builtins = {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'range': range,
            }
            
            # 移除setattr等可能被滥用的函数
            exec(script, {'__builtins__': safe_builtins}, context)
        except Exception as e:
            # 脚本执行错误，记录但不中断测试
            print(f"前置脚本执行错误: {str(e)}")
    
    def _execute_post_script(self) -> None:
        """执行后置脚本（Python脚本）"""
        if not self.testcase.post_script:
            return
        
        script = self.testcase.post_script
        
        # 验证脚本安全性
        if not self._validate_script(script):
            print(f"后置脚本包含不安全操作，已拒绝执行")
            return
        
        # 限制脚本长度，防止资源耗尽
        if len(script) > 10000:  # 10KB限制
            print(f"后置脚本过长（{len(script)}字符），已拒绝执行")
            return
        
        # 准备脚本执行上下文
        context = {
            'status_code': self.response.status_code if self.response else None,
            'headers': dict(self.response.headers) if self.response else {},
            'body': self._get_response_text() if self.response else '',
            'json': None,
            'time': self.execution_result.get('time', 0),
            'response': self.response,
            'variables': self.variables,
            'testcase': self.testcase,
            'api': self.api,
            'environment': self.environment,
            # 提供一些常用函数
            'set_variable': lambda name, value: self.variables.update({name: value}),
            'get_variable': lambda name: self.variables.get(name),
            'get_json_value': lambda path: self._get_json_value(path) if self.response else None,
            'print': print,
        }
        
        # 尝试解析JSON响应
        if self.response:
            try:
                context['json'] = self.response.json()
            except:
                pass
        
        try:
            # 执行脚本（注意：生产环境应该使用更安全的方式）
            safe_builtins = {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'range': range,
                'type': type,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'round': round,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
            }
            
            exec(script, {'__builtins__': safe_builtins}, context)
        except Exception as e:
            # 脚本执行错误，记录但不中断测试
            print(f"后置脚本执行错误: {str(e)}")
    
    def _execute_environment_pre_hook(self, request_info: dict = None) -> None:
        """执行环境前置钩子函数
        
        Args:
            request_info: 当前请求信息，包含 method, url, path, body 等
        """
        if not self.environment or not self.environment.pre_hook:
            return
        
        script = self.environment.pre_hook
        
        # 验证脚本安全性
        if not self._validate_script(script):
            print(f"环境前置钩子包含不安全操作，已拒绝执行")
            return
        
        # 限制脚本长度，防止资源耗尽
        if len(script) > 10000:  # 10KB限制
            print(f"环境前置钩子过长（{len(script)}字符），已拒绝执行")
            return
        
        # 准备脚本执行上下文
        context = {
            'variables': self.variables,
            'testcase': self.testcase,
            'api': self.api,
            'environment': self.environment,
            'request_info': request_info or {},  # 传入请求信息
            'set_variable': lambda name, value: self.variables.update({name: value}),
            'get_variable': lambda name: self.variables.get(name),
            'print': print,
        }
        
        try:
            safe_builtins = {
                'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'range': range,
                'type': type, 'isinstance': isinstance, 'hasattr': hasattr,
                'getattr': getattr, 'setattr': setattr, 'round': round,
                'abs': abs, 'min': min, 'max': max, 'sum': sum,
                # 添加签名所需的模块
                'hmac': __import__('hmac'),
                'hashlib': __import__('hashlib'),
                'base64': __import__('base64'),
                'time': __import__('time'),
                'json': __import__('json'),
                'uuid': __import__('uuid'),
            }
            exec(script, {'__builtins__': safe_builtins}, context)
        except Exception as e:
            print(f"环境前置钩子执行错误: {str(e)}")
    
    def _execute_environment_post_hook(self) -> None:
        """执行环境后置钩子函数"""
        if not self.environment or not self.environment.post_hook:
            return
        
        script = self.environment.post_hook
        
        # 验证脚本安全性
        if not self._validate_script(script):
            print(f"环境后置钩子包含不安全操作，已拒绝执行")
            return
        
        # 限制脚本长度，防止资源耗尽
        if len(script) > 10000:  # 10KB限制
            print(f"环境后置钩子过长（{len(script)}字符），已拒绝执行")
            return
        
        # 准备脚本执行上下文
        context = {
            'status_code': self.response.status_code if self.response else None,
            'headers': dict(self.response.headers) if self.response else {},
            'body': self._get_response_text() if self.response else '',
            'json': None,
            'time': self.execution_result.get('time', 0),
            'response': self.response,
            'variables': self.variables,
            'testcase': self.testcase,
            'api': self.api,
            'environment': self.environment,
            'set_variable': lambda name, value: self.variables.update({name: value}),
            'get_variable': lambda name: self.variables.get(name),
            'get_json_value': lambda path: self._get_json_value(path) if self.response else None,
            'print': print,
        }
        
        # 尝试解析JSON响应
        if self.response:
            try:
                context['json'] = self.response.json()
            except:
                pass
        
        try:
            safe_builtins = {
                'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'range': range,
                'type': type, 'isinstance': isinstance, 'hasattr': hasattr,
                'getattr': getattr, 'setattr': setattr, 'round': round,
                'abs': abs, 'min': min, 'max': max, 'sum': sum,
            }
            exec(script, {'__builtins__': safe_builtins}, context)
        except Exception as e:
            print(f"环境后置钩子执行错误: {str(e)}")
    
    def _execute_manual_assertions(self) -> list:
        """执行手动断言脚本（Python脚本）"""
        manual_assertions = []
        
        # 查找手动断言（type为'manual'或'script'）
        assertions = self.testcase.assertions or []
        manual_scripts = [a for a in assertions if a.get('type') in ['manual', 'script']]
        
        if not manual_scripts:
            return manual_assertions
        
        # 准备断言上下文
        context = {
            'status_code': self.response.status_code if self.response else None,
            'headers': dict(self.response.headers) if self.response else {},
            'body': self._get_response_text() if self.response else '',
            'json': None,
            'time': self.execution_result.get('time', 0),
            'response': self.response,
            'variables': self.variables,
            'testcase': self.testcase,
            'api': self.api,
        }
        
        # 尝试解析JSON响应
        if self.response:
            try:
                context['json'] = self.response.json()
            except:
                pass
        
        # 执行每个手动断言脚本
        for idx, assertion in enumerate(manual_scripts):
            script = assertion.get('script', '')
            description = assertion.get('description', f'手动断言 #{idx + 1}')
            
            if not script:
                continue
            
            # 验证脚本安全性
            if not self._validate_script(script):
                manual_assertions.append({
                    'type': assertion.get('type', 'manual'),
                    'description': description,
                    'success': False,
                    'message': '脚本包含不安全操作，已拒绝执行'
                })
                continue
            
            # 限制脚本长度，防止资源耗尽
            if len(script) > 10000:  # 10KB限制
                manual_assertions.append({
                    'type': assertion.get('type', 'manual'),
                    'description': description,
                    'success': False,
                    'message': f'脚本过长（{len(script)}字符），已拒绝执行'
                })
                continue
            
            try:
                # 使用受限的执行环境（安全的脚本执行）
                # 注意：实际生产环境应该使用更安全的脚本执行方式（如沙箱）
                # 这里提供一个基础实现
                
                # 定义断言辅助函数
                def assert_equal(actual, expected, message=''):
                    if actual != expected:
                        raise AssertionError(f"{message} 期望: {expected}, 实际: {actual}")
                    return True
                
                def assert_not_equal(actual, expected, message=''):
                    if actual == expected:
                        raise AssertionError(f"{message} 不应等于: {expected}, 实际: {actual}")
                    return True
                
                def assert_contains(container, item, message=''):
                    if item not in container:
                        raise AssertionError(f"{message} 期望包含: {item}, 实际: {container}")
                    return True
                
                def assert_greater_than(actual, expected, message=''):
                    if actual <= expected:
                        raise AssertionError(f"{message} 期望 > {expected}, 实际: {actual}")
                    return True
                
                def assert_less_than(actual, expected, message=''):
                    if actual >= expected:
                        raise AssertionError(f"{message} 期望 < {expected}, 实际: {actual}")
                    return True
                
                def assert_true(condition, message=''):
                    if not condition:
                        raise AssertionError(f"{message} 期望为True, 实际为False")
                    return True
                
                def assert_false(condition, message=''):
                    if condition:
                        raise AssertionError(f"{message} 期望为False, 实际为True")
                    return True
                
                # 扩展上下文
                context.update({
                    'assert_equal': assert_equal,
                    'assert_not_equal': assert_not_equal,
                    'assert_contains': assert_contains,
                    'assert_greater_than': assert_greater_than,
                    'assert_less_than': assert_less_than,
                    'assert_true': assert_true,
                    'assert_false': assert_false,
                })
                
                # 执行脚本（注意：生产环境应该使用更安全的方式）
                exec(script, {'__builtins__': {}}, context)
                
                manual_assertions.append({
                    'type': 'manual',
                    'description': description,
                    'success': True,
                    'message': '手动断言通过'
                })
                
            except AssertionError as e:
                manual_assertions.append({
                    'type': 'manual',
                    'description': description,
                    'success': False,
                    'message': str(e)
                })
            except Exception as e:
                manual_assertions.append({
                    'type': 'manual',
                    'description': description,
                    'success': False,
                    'message': f'脚本执行错误: {str(e)}'
                })
        
        return manual_assertions
    
    def _validate_assertions(self) -> list:
        """验证断言（只处理常规断言，手动断言由_execute_manual_assertions处理）"""
        assertions_result = []
        assertions = self.testcase.assertions or []
        
        # 过滤掉手动断言类型
        regular_assertions = [a for a in assertions if a.get('type') not in ['manual', 'script']]
        
        if not self.response:
            return assertions_result
        
        for assertion in regular_assertions:
            assertion_type = assertion.get('type')
            expected = assertion.get('expected')
            actual = None
            success = False
            message = ''
            
            try:
                if assertion_type == 'status_code':
                    # 状态码断言
                    actual = self.response.status_code
                    # 统一转换为整数进行比较
                    expected_int = int(expected) if expected is not None else None
                    success = actual == expected_int
                    message = f"状态码断言: 期望 {expected_int}, 实际 {actual}"
                
                elif assertion_type == 'response_time':
                    # 响应时间断言（毫秒）
                    actual = self.execution_result['time']
                    # 统一转换为数值进行比较
                    expected_num = float(expected) if expected is not None else None
                    success = actual <= expected_num if expected_num is not None else False
                    message = f"响应时间断言: 期望 <= {expected_num}ms, 实际 {actual}ms"
                
                elif assertion_type == 'contains':
                    # 响应体包含断言
                    response_text = self._get_response_text()
                    success = expected in response_text
                    actual = response_text
                    message = f"包含断言: 期望包含 '{expected}'"
                
                elif assertion_type == 'json_path':
                    # JSON 路径断言
                    json_path = assertion.get('path') or assertion.get('json_path', '')
                    # 去掉$.前缀（如果有）
                    clean_path = json_path[2:] if json_path.startswith('$.') else json_path
                    # 支持expected或value字段
                    expected_value = assertion.get('expected') or assertion.get('value')
                    operator = assertion.get('operator', 'equals')
                    actual = self._get_json_value(clean_path)
                    
                    if operator == 'exists':
                        # 检查字段是否存在
                        success = actual is not None
                        message = f"JSON路径断言 {json_path}: 期望存在, 实际 {'存在' if success else '不存在'}"
                    elif operator == 'contains':
                        # 包含断言
                        expected_str = str(expected_value) if expected_value else ''
                        actual_str = str(actual) if actual else ''
                        success = expected_str in actual_str
                        message = f"JSON路径断言 {json_path}: 期望包含 '{expected_str}', 实际 '{actual_str}'"
                    else:
                        # 默认相等断言
                        success = str(actual) == str(expected_value)
                        message = f"JSON路径断言 {json_path}: 期望 {expected_value}, 实际 {actual}"
                
                elif assertion_type == 'equals':
                    # 相等断言
                    json_path = assertion.get('json_path', '')
                    if json_path:
                        actual = self._get_json_value(json_path)
                    else:
                        actual = self._get_response_text()
                    success = str(actual) == str(expected)
                    message = f"相等断言: 期望 {expected}, 实际 {actual}"
                
            except Exception as e:
                success = False
                message = f"断言执行错误: {str(e)}"
            
            assertions_result.append({
                'type': assertion_type,
                'expected': expected,
                'actual': actual,
                'success': success,
                'message': message
            })
        
        return assertions_result
    
    def _get_response_text(self) -> str:
        """获取响应文本"""
        if not self.response:
            return ''
        
        try:
            return self.response.text
        except:
            return ''
    
    def _get_json_value(self, json_path: str) -> Any:
        """根据JSON路径获取值"""
        try:
            data = self.response.json()
            # 简单的 JSON 路径实现，支持 . 分隔
            keys = json_path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list):
                    try:
                        value = value[int(key)]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None
            return value
        except:
            return None
    
    def execute(self) -> Dict[str, Any]:
        """执行测试用例"""
        try:
            # 先构建基础请求参数（环境钩子可能需要这些信息）
            url = self._build_url()
            
            # 方案A：优先级：用例覆盖 > 接口定义
            if self.testcase.body_override:
                body = self._replace_variables_in_dict(self.testcase.body_override)
            else:
                body = self._replace_variables_in_dict(self.api.body or {})
            
            # 提取path（去掉域名和context-path）
            import re
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            path = parsed_url.path
            # 去掉常见的context-path
            path = re.sub(r'^/crex-java', '', path)
            
            # 准备请求信息供环境钩子使用
            request_info = {
                'method': self.api.method,
                'url': url,
                'path': path,
                'body': body,
                'api': self.api,
                'testcase': self.testcase
            }
            
            # 执行环境前置钩子（传入请求信息）
            self._execute_environment_pre_hook(request_info)
            
            # 执行前置脚本
            self._execute_pre_script()
            
            # 重新构建headers（因为环境钩子可能设置了签名变量）
            headers = self._build_headers()
            
            # 方案A：优先级：用例覆盖 > 接口定义
            if self.testcase.params_override:
                params = self._replace_variables_in_dict(self.testcase.params_override)
            else:
                params = self._replace_variables_in_dict(self.api.params or {})
            
            if self.testcase.body_override:
                body = self._replace_variables_in_dict(self.testcase.body_override)
            else:
                body = self._replace_variables_in_dict(self.api.body or {})
            
            auth = self._build_auth()
            
            # 准备请求数据
            request_kwargs = {
                'method': self.api.method,
                'url': url,
                'headers': headers,
                'params': params,
                'timeout': 30,
                'verify': False  # 禁用SSL验证（开发环境，生产环境建议启用）
            }
            
            # 添加认证
            if auth:
                if isinstance(auth, tuple) and len(auth) == 2:
                    if auth[0] == 'Bearer':
                        # Bearer Token: Authorization: Bearer <token>
                        headers['Authorization'] = f'Bearer {auth[1]}'
                    elif auth[0] == 'Token':
                        # Django REST Framework Token: Authorization: Token <token>
                        headers['Authorization'] = f'Token {auth[1]}'
                    else:
                        # Basic Auth 使用 requests 的 auth 参数
                        request_kwargs['auth'] = auth
            
            # 处理自定义 Header Token (auth_type='header')
            if self.api.auth_type and self.api.auth_type.lower() == 'header':
                auth_config = self.api.auth_config or {}
                header_name = auth_config.get('header_name', 'Authorization')
                token = auth_config.get('token', '')
                if not token:
                    token = self.variables.get('token') or self.variables.get('access_token')
                if token:
                    token = self._replace_variables(str(token))
                    token_format = auth_config.get('format', 'Bearer')  # 默认 Bearer 格式
                    headers[header_name] = f'{token_format} {token}' if token_format else token
            
            # 处理全局 Token 的 Header 类型（优先使用动态Token）
            # 注意：全局Token的variables已在__init__中注入，这里只处理认证Header
            if not self.api.auth_type or (self.api.auth_type and self.api.auth_type.lower() != 'header'):
                global_token = self._get_global_token()
                if global_token and global_token.auth_type == 'header':
                    # 【优化】优先使用动态Token
                    dynamic_token = self.variables.get('token')
                    global_token_static = self.variables.get('_global_token_static')
                    
                    if dynamic_token and dynamic_token != global_token_static:
                        # 使用动态Token
                        token_value = self._replace_variables(str(dynamic_token))
                    else:
                        # 使用全局Token的静态值
                        token_value = global_token.token
                        token_value = self._replace_variables(token_value)
                    
                    token_format = global_token.token_format or 'Bearer'
                    header_name = global_token.header_name or 'Authorization'
                    headers[header_name] = f'{token_format} {token_value}' if token_format else token_value
            
            # 添加请求体
            if self.api.method in ['POST', 'PUT', 'PATCH']:
                if body:
                    request_kwargs['json'] = body
            
            # 发送请求（只计算HTTP请求的实际时间）
            # 使用Session来复用连接，减少连接建立时间
            # response.elapsed 包含：HTTP请求发送、服务器处理、响应接收
            # 对于新连接，也会包含TCP连接建立时间
            # 但不包括：前置脚本、后置脚本、变量提取、断言验证等平台处理时间
            session = get_session()
            method = request_kwargs.pop('method')
            self.response = session.request(method=method, **request_kwargs)
            
            # 使用response.elapsed获取真实的HTTP请求时间（不包括平台处理时间）
            # response.elapsed是timedelta对象，表示从开始发送请求到收到响应的时间
            # 对于复用连接的情况，不包含连接建立时间，更准确地反映API响应时间
            http_request_time_ms = self.response.elapsed.total_seconds() * 1000  # 转换为毫秒
            
            # 保存响应信息
            response_json = None
            try:
                # 尝试解析JSON响应
                response_json = self.response.json()
            except:
                pass
            
            self.execution_result.update({
                'status_code': self.response.status_code,
                'headers': dict(self.response.headers),
                'body': self._get_response_text(),
                'json': response_json,  # 保存解析后的JSON对象
                'time': round(http_request_time_ms, 2),  # 只记录HTTP请求的实际时间
                'url': url
            })
            
            # 从响应中提取变量
            self._extract_variables()
            
            # 验证断言
            assertions_result = self._validate_assertions()
            
            # 执行手动断言脚本
            manual_assertions = self._execute_manual_assertions()
            
            # 合并所有断言结果
            all_assertions = assertions_result + manual_assertions
            self.execution_result['assertions'] = all_assertions
            
            # 判断是否通过（所有断言都通过且状态码为2xx）
            all_assertions_passed = all(a['success'] for a in all_assertions) if all_assertions else True
            status_code_ok = 200 <= self.response.status_code < 300
            
            self.execution_result['success'] = all_assertions_passed and status_code_ok
            
            # 执行后置脚本
            self._execute_post_script()
            
            # 执行环境后置钩子
            self._execute_environment_post_hook()
            
            # 将提取的变量保存到执行结果中，供后续测试用例使用
            self.execution_result['extracted_variables'] = self.variables.copy()
            
        except requests.exceptions.Timeout as e:
            self.execution_result['error'] = f'请求超时: {str(e)}'
            # 超时情况无法获取准确时间，记录超时时间（30秒）
            self.execution_result['time'] = 30000  # 30秒超时
            self.execution_result['url'] = url if 'url' in locals() else '未知'
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            # 提供更友好的错误信息
            if 'SSLError' in error_msg or 'CERTIFICATE' in error_msg:
                error_msg = 'SSL证书验证失败，请检查证书或禁用SSL验证'
            elif 'Name or service not known' in error_msg:
                error_msg = '无法解析域名，请检查URL是否正确'
            else:
                error_msg = f'连接错误: {error_msg}'
            self.execution_result['error'] = error_msg
            # 连接错误时无法获取准确时间，设为0
            self.execution_result['time'] = 0
            self.execution_result['url'] = url if 'url' in locals() else '未知'
        except requests.exceptions.RequestException as e:
            self.execution_result['error'] = f'请求异常: {str(e)}'
            # 请求异常时无法获取准确时间，设为0
            self.execution_result['time'] = 0
            self.execution_result['url'] = url if 'url' in locals() else '未知'
        except Exception as e:
            import traceback
            self.execution_result['error'] = f'执行错误: {str(e)}'
            self.execution_result['traceback'] = traceback.format_exc()
            # 其他异常时无法获取准确时间，设为0
            self.execution_result['time'] = 0
            self.execution_result['url'] = url if 'url' in locals() else '未知'
        
        return self.execution_result


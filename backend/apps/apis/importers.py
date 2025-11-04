"""
接口导入工具
支持 Postman Collection v2.1 和 Swagger/OpenAPI 3.0 格式
"""
import json
import yaml
from typing import Dict, List, Any
from .models import API


class PostmanImporter:
    """Postman Collection v2.1 导入器"""
    
    def __init__(self, project):
        self.project = project
        self.imported_apis = []
    
    def import_collection(self, collection_data: Dict) -> List[API]:
        """导入Postman Collection"""
        if isinstance(collection_data, str):
            collection_data = json.loads(collection_data)
        
        # 验证是否为Postman Collection格式
        if 'info' not in collection_data:
            raise ValueError('不是有效的Postman Collection格式')
        
        # 解析Collection中的items
        items = collection_data.get('item', [])
        self._parse_items(items)
        
        return self.imported_apis
    
    def _parse_items(self, items: List, folder_prefix: str = ''):
        """递归解析items（支持文件夹）"""
        for item in items:
            if 'item' in item:
                # 这是一个文件夹，递归处理
                folder_name = item.get('name', 'Folder')
                new_prefix = f"{folder_prefix}/{folder_name}" if folder_prefix else folder_name
                self._parse_items(item['item'], new_prefix)
            elif 'request' in item:
                # 这是一个请求
                api = self._parse_request(item, folder_prefix)
                if api:
                    self.imported_apis.append(api)
    
    def _parse_request(self, item: Dict, folder_prefix: str) -> API:
        """解析单个请求"""
        request = item.get('request', {})
        
        # 获取基本信息
        name = item.get('name', 'Unnamed API')
        if folder_prefix:
            name = f"{folder_prefix}/{name}"
        
        # 解析URL
        url = request.get('url', {})
        if isinstance(url, str):
            api_url = url
        elif isinstance(url, dict):
            # URL是对象格式，优先使用raw字段
            raw_url = url.get('raw', '')
            if raw_url:
                # 如果是完整URL，保留完整URL；如果是路径，只保留路径
                api_url = raw_url
            else:
                # 从path数组构建URL
                path_parts = url.get('path', [])
                # 过滤掉协议相关的部分（如"https:", "", "domain.com"）
                clean_parts = [p for p in path_parts if p and not p.endswith(':') and '.' not in p]
                api_url = '/' + '/'.join(clean_parts) if clean_parts else '/'
        else:
            api_url = '/'
        
        # 解析方法
        method = request.get('method', 'GET').upper()
        
        # 解析请求头
        headers = {}
        for header in request.get('header', []):
            if not header.get('disabled', False):
                headers[header.get('key', '')] = header.get('value', '')
        
        # 解析查询参数
        params = {}
        if isinstance(url, dict):
            for query in url.get('query', []):
                if not query.get('disabled', False):
                    params[query.get('key', '')] = query.get('value', '')
        
        # 解析请求体
        body_data = {}
        request_body = request.get('body', {})
        if request_body:
            mode = request_body.get('mode', '')
            if mode == 'raw':
                # JSON格式
                raw_data = request_body.get('raw', '')
                if raw_data:
                    try:
                        body_data = json.loads(raw_data)
                    except:
                        pass
            elif mode == 'formdata':
                # 表单数据
                for form_item in request_body.get('formdata', []):
                    if not form_item.get('disabled', False):
                        body_data[form_item.get('key', '')] = form_item.get('value', '')
            elif mode == 'urlencoded':
                # URL编码数据
                for form_item in request_body.get('urlencoded', []):
                    if not form_item.get('disabled', False):
                        body_data[form_item.get('key', '')] = form_item.get('value', '')
        
        # 解析描述
        description = item.get('request', {}).get('description', '') or ''
        
        # 创建API对象（不保存到数据库）
        api = API(
            name=name,
            url=api_url,
            method=method,
            project=self.project,
            description=description,
            headers=headers,
            params=params,
            body=body_data
        )
        
        return api


class SwaggerImporter:
    """Swagger/OpenAPI 3.0 导入器"""
    
    def __init__(self, project):
        self.project = project
        self.imported_apis = []
    
    def import_spec(self, spec_data: Any) -> List[API]:
        """导入Swagger/OpenAPI规范"""
        if isinstance(spec_data, str):
            # 尝试解析YAML或JSON
            try:
                spec_data = yaml.safe_load(spec_data)
            except:
                try:
                    spec_data = json.loads(spec_data)
                except:
                    raise ValueError('无法解析Swagger/OpenAPI文档，请确保是有效的YAML或JSON格式')
        
        # 验证OpenAPI版本
        openapi_version = spec_data.get('openapi', '') or spec_data.get('swagger', '')
        if not openapi_version:
            raise ValueError('不是有效的Swagger/OpenAPI格式')
        
        # 解析paths
        paths = spec_data.get('paths', {})
        self._parse_paths(paths, spec_data)
        
        return self.imported_apis
    
    def _parse_paths(self, paths: Dict, spec_data: Dict):
        """解析paths"""
        for path, path_item in paths.items():
            # 遍历每个HTTP方法
            for method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                if method in path_item:
                    operation = path_item[method]
                    api = self._parse_operation(path, method.upper(), operation, spec_data)
                    if api:
                        self.imported_apis.append(api)
    
    def _parse_operation(self, path: str, method: str, operation: Dict, spec_data: Dict) -> API:
        """解析单个操作"""
        # 获取摘要和描述
        summary = operation.get('summary', '')
        description = operation.get('description', '')
        
        # 获取tags（模块/分组）
        tags = operation.get('tags', [])
        tag_prefix = ''
        if tags and len(tags) > 0:
            # 使用第一个tag作为模块名
            tag_prefix = f"[{tags[0]}] "
        
        # 组合名称：[模块] 接口摘要
        name = f"{tag_prefix}{summary}" if summary else f"{tag_prefix}{method} {path}"
        
        # 解析参数
        params = {}
        headers = {}
        body_data = {}
        
        for param in operation.get('parameters', []):
            param_name = param.get('name', '')
            param_in = param.get('in', '')
            param_example = param.get('example', '')
            
            if param_in == 'query':
                params[param_name] = param_example or ''
            elif param_in == 'header':
                headers[param_name] = param_example or ''
        
        # 解析请求体（OpenAPI 3.0）
        request_body = operation.get('requestBody', {})
        if request_body:
            content = request_body.get('content', {})
            # 优先处理JSON
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                body_data = self._schema_to_example(schema, spec_data)
        
        # 创建API对象（不保存到数据库）
        api = API(
            name=name,
            url=path,
            method=method,
            project=self.project,
            description=description,
            headers=headers,
            params=params,
            body=body_data
        )
        
        return api
    
    def _schema_to_example(self, schema: Dict, spec_data: Dict) -> Any:
        """将schema转换为示例数据"""
        # 如果有example，直接使用
        if 'example' in schema:
            return schema['example']
        
        # 如果有$ref，解析引用
        if '$ref' in schema:
            ref_path = schema['$ref']
            # 解析引用（如 #/components/schemas/User）
            ref_parts = ref_path.split('/')
            if ref_parts[0] == '#':
                # 内部引用
                ref_data = spec_data
                for part in ref_parts[1:]:
                    ref_data = ref_data.get(part, {})
                return self._schema_to_example(ref_data, spec_data)
        
        # 根据类型生成示例
        schema_type = schema.get('type', 'object')
        
        if schema_type == 'object':
            properties = schema.get('properties', {})
            result = {}
            for prop_name, prop_schema in properties.items():
                result[prop_name] = self._schema_to_example(prop_schema, spec_data)
            return result
        elif schema_type == 'array':
            items_schema = schema.get('items', {})
            return [self._schema_to_example(items_schema, spec_data)]
        elif schema_type == 'string':
            return schema.get('default', '')
        elif schema_type == 'integer':
            return schema.get('default', 0)
        elif schema_type == 'number':
            return schema.get('default', 0.0)
        elif schema_type == 'boolean':
            return schema.get('default', False)
        else:
            return None


"""
接口导出工具
支持导出为 Postman Collection v2.1 格式
"""
import json
from typing import List
from .models import API


class PostmanExporter:
    """Postman Collection v2.1 导出器"""
    
    def __init__(self, apis: List[API], collection_name: str = 'Exported Collection'):
        self.apis = apis
        self.collection_name = collection_name
    
    def export(self) -> str:
        """导出为Postman Collection JSON"""
        collection = {
            'info': {
                'name': self.collection_name,
                '_postman_id': self._generate_id(),
                'description': '从BenchLink导出的接口集合',
                'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
            },
            'item': []
        }
        
        # 按项目分组
        project_groups = {}
        for api in self.apis:
            project_name = api.project.name if api.project else 'Default'
            if project_name not in project_groups:
                project_groups[project_name] = []
            project_groups[project_name].append(api)
        
        # 为每个项目创建文件夹
        for project_name, apis in project_groups.items():
            folder = {
                'name': project_name,
                'item': []
            }
            
            for api in apis:
                folder['item'].append(self._api_to_request(api))
            
            collection['item'].append(folder)
        
        return json.dumps(collection, indent=2, ensure_ascii=False)
    
    def _api_to_request(self, api: API) -> dict:
        """将API转换为Postman请求"""
        # 构建URL
        url_obj = {
            'raw': api.url,
            'protocol': 'https',
            'host': [],
            'path': api.url.strip('/').split('/'),
            'query': []
        }
        
        # 添加查询参数
        if api.params:
            for key, value in api.params.items():
                url_obj['query'].append({
                    'key': key,
                    'value': str(value),
                    'disabled': False
                })
        
        # 构建请求头
        headers = []
        if api.headers:
            for key, value in api.headers.items():
                headers.append({
                    'key': key,
                    'value': str(value),
                    'type': 'text',
                    'disabled': False
                })
        
        # 构建请求体
        body = {}
        if api.method in ['POST', 'PUT', 'PATCH'] and api.body:
            body = {
                'mode': 'raw',
                'raw': json.dumps(api.body, indent=2, ensure_ascii=False),
                'options': {
                    'raw': {
                        'language': 'json'
                    }
                }
            }
        
        # 构建请求
        request = {
            'name': api.name,
            'request': {
                'method': api.method,
                'header': headers,
                'body': body,
                'url': url_obj,
                'description': api.description or ''
            },
            'response': []
        }
        
        return request
    
    def _generate_id(self) -> str:
        """生成UUID"""
        import uuid
        return str(uuid.uuid4())


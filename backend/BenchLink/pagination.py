"""
自定义分页类
"""
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """支持客户端设置页面大小的分页类"""
    page_size = 20  # 默认每页显示20条
    page_size_query_param = 'page_size'  # 允许客户端通过page_size参数修改每页数量
    max_page_size = 10000  # 最大每页显示10000条（足够获取所有接口）
    page_query_param = 'page'  # 页码参数名


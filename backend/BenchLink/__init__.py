import pymysql

# 使用PyMySQL替代MySQLdb
pymysql.install_as_MySQLdb()

# 尝试导入Celery，如果Redis未运行则跳过（不影响Django启动）
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except Exception as e:
    # Redis未运行时，Celery导入会失败，但不影响Django启动
    import warnings
    warnings.warn(f'Celery未初始化: {e}. Django仍可正常运行，但异步任务功能不可用。')
    __all__ = ()




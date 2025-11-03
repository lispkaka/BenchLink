"""
自定义runserver命令，允许在数据库连接失败时也能启动服务
"""
from django.core.management.commands.runserver import Command as RunserverCommand
from django.db import connections
from django.db.utils import OperationalError
import warnings


class Command(RunserverCommand):
    """继承runserver命令，但跳过迁移检查"""
    
    def check_migrations(self):
        """
        重写迁移检查方法，允许数据库连接失败
        """
        try:
            # 尝试检查迁移
            super().check_migrations()
        except OperationalError as e:
            # 数据库连接失败时，只发出警告，不阻止启动
            warnings.warn(
                f'数据库连接失败，跳过迁移检查: {e}\n'
                '服务将继续启动，但API功能可能会受限。\n'
                '请检查数据库配置并确保数据库服务正在运行。',
                UserWarning
            )
        except Exception as e:
            # 其他异常也捕获，避免阻止启动
            warnings.warn(
                f'迁移检查失败: {e}\n'
                '服务将继续启动。',
                UserWarning
            )


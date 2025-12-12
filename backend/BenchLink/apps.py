from django.apps import AppConfig
import os
from django.conf import settings


class BenchLinkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'BenchLink'
    verbose_name = 'BenchLink'

    def ready(self):
        """应用启动时初始化调度器"""
        # 避免在迁移时启动调度器
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        # 在开发模式下，Django runserver 会启动两个进程（自动重载），防止调度器被重复启动导致任务重复执行
        if settings.DEBUG and os.environ.get('RUN_MAIN') != 'true':
            return

        try:
            from apps.scheduler.tasks import start_scheduler
            start_scheduler()
        except Exception as e:
            # 如果调度器启动失败，记录警告但不影响Django启动
            import warnings
            warnings.warn(f'调度器初始化失败: {e}. Django仍可正常运行，但定时任务功能不可用。')


# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0002_api_parameterized_data_api_parameterized_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='api',
            name='files',
            field=models.JSONField(blank=True, default=dict, help_text='格式: {"field_name": {"file_path": "/path/to/file", "content_type": "image/jpeg"}}', verbose_name='文件上传配置'),
        ),
    ]


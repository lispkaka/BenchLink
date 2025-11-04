# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0004_performancetest'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcase',
            name='files_override',
            field=models.JSONField(blank=True, default=dict, help_text='覆盖接口定义的文件上传配置，支持${variable}变量，留空则使用接口定义的文件配置', verbose_name='文件上传覆盖（支持变量）'),
        ),
    ]


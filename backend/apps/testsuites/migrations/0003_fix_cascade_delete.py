# Generated manually to fix cascade delete constraints
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsuites', '0002_add_testcase_order'),
        ('testcases', '0001_initial'),
    ]

    operations = [
        # 删除旧的外键约束
        migrations.RunSQL(
            sql=[
                "ALTER TABLE testsuites_testsuite_testcases DROP FOREIGN KEY testsuites_testsuite_testsuite_id_57a4bcd4_fk_testsuite;",
                "ALTER TABLE testsuites_testsuite_testcases DROP FOREIGN KEY testsuites_testsuite_testcase_id_c9cfe338_fk_testcases;",
            ],
            reverse_sql=[
                # 回滚时不需要做什么，因为下面会重新创建
            ],
        ),
        # 重新创建带CASCADE的外键约束
        migrations.RunSQL(
            sql=[
                "ALTER TABLE testsuites_testsuite_testcases ADD CONSTRAINT testsuites_testsuite_testsuite_id_57a4bcd4_fk_testsuite FOREIGN KEY (testsuite_id) REFERENCES testsuites_testsuite(id) ON DELETE CASCADE;",
                "ALTER TABLE testsuites_testsuite_testcases ADD CONSTRAINT testsuites_testsuite_testcase_id_c9cfe338_fk_testcases FOREIGN KEY (testcase_id) REFERENCES testcases_testcase(id) ON DELETE CASCADE;",
            ],
            reverse_sql=[
                "ALTER TABLE testsuites_testsuite_testcases DROP FOREIGN KEY testsuites_testsuite_testsuite_id_57a4bcd4_fk_testsuite;",
                "ALTER TABLE testsuites_testsuite_testcases DROP FOREIGN KEY testsuites_testsuite_testcase_id_c9cfe338_fk_testcases;",
            ],
        ),
    ]


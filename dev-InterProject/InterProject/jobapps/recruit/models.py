from django.db import models

from jobapps.job.models import Job
from jobapps.student.models import Student


class Recruit(models.Model):
    # 投递状态(0表示未阅读,1表示已阅读)
    status = models.IntegerField(default=0)
    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', help_text='创建时间', null=True)
    # 外键
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='学生', blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name='职位', blank=True)

    class Meta:
        verbose_name = "简历投递表"
        verbose_name_plural = verbose_name
        ordering = ['id']
        db_table = 'recruit'  # 对应的数据库表名

    def __str__(self):
        return self.status

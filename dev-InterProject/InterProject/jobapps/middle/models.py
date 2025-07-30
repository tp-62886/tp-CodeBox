from django.db import models

from jobapps.job.models import Job
from jobapps.student.models import Student


class ClickJob(models.Model):  # 学生浏览职位
    satisfied = models.CharField(max_length=10, verbose_name='是否交互', default=1)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', help_text='创建时间', null=True)
    # 创建时间
    # 外键
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='学生id', null=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name='id', blank=True, null=True)

    class Meta:
        verbose_name = "学生浏览职位"
        verbose_name_plural = verbose_name
        db_table = 'click_job'  # 对应的数据库表名


class StarJob(models.Model):  # 学生收藏职位
    satisfied = models.CharField(max_length=10, verbose_name='是否交互', null=True)
    # 外键
    SID = models.ForeignKey(Student, to_field='SID', db_column='SID', on_delete=models.CASCADE, verbose_name='学生学号',
                            blank=True)
    DWZZJGDM = models.ForeignKey(Job, to_field='DWZZJGDM', db_column='DWZZJGDM', on_delete=models.CASCADE,
                                 verbose_name='职位编号', blank=True)

    class Meta:
        verbose_name = "学生收藏职位"
        verbose_name_plural = verbose_name
        db_table = 'star_job'


class ClickStudent(models.Model):  # 公司浏览学生
    satisfied = models.CharField(max_length=10, verbose_name='是否交互', null=True)
    # 外键
    SID = models.ForeignKey(Student, to_field='SID', db_column='SID', on_delete=models.CASCADE, verbose_name='学生学号',
                            blank=True)
    DWZZJGDM = models.ForeignKey(Job, to_field='DWZZJGDM', db_column='DWZZJGDM', on_delete=models.CASCADE,
                                 verbose_name='职位编号', blank=True)

    class Meta:
        verbose_name = "公司浏览学生"
        verbose_name_plural = verbose_name
        db_table = 'click_student'  # 对应的数据库表名


class CompanyCode(models.Model):  # 社会信用代码-企业id
    # 对应的企业id
    COMPANYID = models.CharField(max_length=255, verbose_name='企业id', help_text='企业id', null=True)

    # 社会统一信用代码
    SHTYXYDM = models.CharField(max_length=255, verbose_name='社会统一信用代码', help_text='社会统一信用代码', null=True)

    class Meta:
        verbose_name = "社会信用代码-企业id"
        verbose_name_plural = verbose_name
        db_table = 'company_code'  # 对应的数据库表名

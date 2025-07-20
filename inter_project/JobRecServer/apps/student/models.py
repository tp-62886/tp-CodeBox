from django.conf import settings
from django.db import models


class Student(models.Model):  # 学生信息表
    SID = models.CharField(max_length=255, verbose_name='学号', help_text='学号', null=True, unique=True)
    REALNAME = models.CharField(max_length=100, verbose_name='学生姓名', help_text='学生姓名', null=True)
    GRADE = models.CharField(max_length=255, verbose_name='毕业年份', help_text='毕业年份', null=True)
    DEPARTMENT = models.CharField(max_length=20, verbose_name='学院', help_text='学院', null=True)
    MAJOR = models.CharField(max_length=255, verbose_name='专业', help_text='专业', null=True)
    ZYFX = models.CharField(max_length=255, verbose_name='专业方向', help_text='专业方向', null=True)
    XBMC = models.CharField(max_length=1, verbose_name='性别', help_text='性别', null=True)
    ZXWYYZMC = models.CharField(max_length=10, verbose_name='主修外语', help_text='主修外语', null=True)
    BIRTHDAY = models.CharField(max_length=20, verbose_name='出生年月', help_text='出生年月', null=True)
    XLMC = models.CharField(max_length=10, verbose_name='学历', help_text='学历', null=True)
    XXXSMC = models.CharField(max_length=10, verbose_name='学习形式', help_text='学习形式', null=True)
    JTDZ = models.CharField(max_length=255, verbose_name='家庭住址', help_text='家庭住址', null=True)
    GZZWLBMC = models.CharField(max_length=255, verbose_name='实习过的工作', help_text='实习过的工作', null=True)
    # 手机号
    phone = models.CharField(max_length=255, verbose_name='手机号码', help_text='手机号码', null=True)
    # 外键
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户id', null=True)

    class Meta:
        verbose_name = "学生信息"
        verbose_name_plural = verbose_name
        ordering = ['id']
        db_table = 'student'  # 对应的数据库表名

    def __str__(self):
        return self.REALNAME

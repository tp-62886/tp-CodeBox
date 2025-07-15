from django.db import models
from django.conf import settings


class Company(models.Model):
    name = models.CharField(max_length=255, verbose_name='公司名', null=True)
    unifiedCode = models.CharField(max_length=255, verbose_name='统一社会信用代码', null=True)
    email = models.CharField(max_length=255, verbose_name='单位注册邮箱', null=True)
    # 时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    # 对应的企业id
    COMPANYID = models.CharField(max_length=255, verbose_name='企业id', help_text='企业id', null=True)
    # 外键
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户id', null=True)

    class Meta:
        verbose_name = "公司信息"
        verbose_name_plural = verbose_name
        ordering = ['id']
        db_table = 'company'  # 对应的数据库表名

    def __str__(self):
        return self.name

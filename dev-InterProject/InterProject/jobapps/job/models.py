from django.db import models

from jobapps.company.models import Company


class Job(models.Model):
    DWZZJGDM = models.CharField(max_length=255, verbose_name='职位编号', help_text='职位编号', null=True, unique=True)
    SJDWMC = models.CharField(max_length=255, verbose_name='公司名', help_text='公司名', null=True)
    DWXZMC = models.CharField(max_length=255, verbose_name='公司性质', help_text='公司性质', null=True)
    DWHYMC = models.CharField(max_length=255, verbose_name='公司所属行业', help_text='公司所属行业', null=True)
    GZZWLBMC = models.CharField(max_length=255, verbose_name='职位名', help_text='职位名', null=True)
    DWSZDDM = models.CharField(max_length=255, verbose_name='工作地址', help_text='工作地址', null=True)
    # 扩充字段
    major = models.TextField(verbose_name='需求专业', help_text='需求专业', null=True)
    salary = models.CharField(max_length=255, verbose_name='薪资', help_text='薪资', null=True)
    degree = models.CharField(max_length=255, verbose_name='学历', help_text='学历', null=True)
    workNature = models.CharField(max_length=255, verbose_name='工作性质', help_text='工作性质', null=True)
    desc = models.TextField(verbose_name='职位描述', help_text='职位描述', null=True)
    # 职位发布时间
    create_time = models.DateTimeField(verbose_name='职位发布时间', help_text='职位发布时间', null=True)
    # 对应的企业id
    COMPANYID = models.CharField(max_length=255, verbose_name='企业id', help_text='企业id', null=True)
    # 外键
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='用户id', null=True)

    # todo 新增字段
    NUM = models.IntegerField(verbose_name='招聘人数', help_text='招聘人数', default=1)

    class Meta:
        verbose_name = "职位信息"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
        db_table = 'job'  # 对应的数据库表名

    def __str__(self):
        return self.GZZWLBMC

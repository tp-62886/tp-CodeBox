from django.db import models


class Work(models.Model):
    companyName = models.CharField(max_length=255, verbose_name='单位名称', help_text='单位名称', null=True)
    workName = models.CharField(max_length=255, verbose_name='职位名称', help_text='职位名称', null=True)
    workNum = models.CharField(max_length=255, verbose_name='职位数', help_text='职位数', null=True)
    major = models.TextField(verbose_name='需求专业', help_text='需求专业', null=True)
    salary = models.CharField(max_length=255, verbose_name='薪资', help_text='薪资', null=True)
    degree = models.CharField(max_length=255, verbose_name='学历', help_text='学历', null=True)
    workNature = models.CharField(max_length=255, verbose_name='工作性质', help_text='工作性质', null=True)
    desc = models.TextField(verbose_name='职位描述', help_text='职位描述', null=True)

    # time = models.DateTimeField(auto_now_add=True, verbose_name='发布时间', help_text='发布时间', null=True)

    class Meta:
        verbose_name = "职位详情"
        verbose_name_plural = verbose_name
        ordering = ['id']
        db_table = 'work'  # 对应的数据库表名

    def __str__(self):
        return self.workName

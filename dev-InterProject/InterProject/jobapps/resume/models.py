from django.db import models

from jobapps.student.models import Student


class Resume(models.Model):  # 学生信息表
    # personalAdvantage = models.CharField(max_length=255, verbose_name='个人优势', help_text='个人优势', null=True)
    # schoolExperience = models.CharField(max_length=255, verbose_name='学校经历', help_text='学校经历', null=True)
    # expectedPositions = models.CharField(max_length=255, verbose_name='期望职位', help_text='期望职位', null=True)
    # skills = models.CharField(max_length=255, verbose_name='掌握技能', help_text='掌握技能', null=True)

    personalAdvantage = models.TextField(verbose_name='个人优势', help_text='个人优势', null=True)
    schoolExperience = models.TextField(verbose_name='学校经历', help_text='学校经历', null=True)
    skills = models.TextField(max_length=255, verbose_name='掌握技能', help_text='掌握技能', null=True)

    # 学生选择期望职位
    expectedPositions = models.TextField(verbose_name='期望职位', help_text='期望职位', null=True)

    # 外键
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='学生学号', null=True)

    class Meta:
        verbose_name = "学生简历"
        verbose_name_plural = verbose_name
        ordering = ['id']
        db_table = 'resume'  # 对应的数据库表名

    def __str__(self):
        return self.personalAdvantage

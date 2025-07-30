from django.db import models
from django.contrib.auth.models import AbstractUser


# 继承AbstractUser
class User(AbstractUser):
    type = models.CharField(max_length=1, verbose_name='用户类型,0学生1企业', default='0')
    sid = models.CharField(max_length=255, verbose_name='学生或企业的唯一标识')

    class Meta:
        verbose_name = '用户'
        db_table = 'user'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


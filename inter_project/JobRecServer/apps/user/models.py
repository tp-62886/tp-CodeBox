from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission# 解决groups，user_permissions冲突(临时使用)


# 继承AbstractUser
class User(AbstractUser):
    type = models.CharField(max_length=1, verbose_name='用户类型,0学生1企业', default='0')
    sid = models.CharField(max_length=255, verbose_name='学生或企业的唯一标识')
# 解决groups冲突(临时使用)
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name="custom_user_groups",  # 唯一名称
        related_query_name="custom_user",
    )
    
    # 解决user_permissions冲突(临时使用)
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name="custom_user_permissions",  # 唯一名称
        related_query_name="custom_user",
    )
    class Meta:
        verbose_name = '用户'
        db_table = 'user'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


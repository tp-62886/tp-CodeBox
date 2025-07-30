from rest_framework import serializers

from jobapps.company.models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class SaveCompanySerializer(serializers.Serializer):  # 注册公司账号
    username = serializers.CharField(help_text="公司账号")
    password = serializers.CharField(help_text="密码")
    name = serializers.CharField(help_text="公司名称")
    confirmPassword = serializers.CharField(help_text="确认密码")
    unifiedCode = serializers.CharField(help_text="统一社会信用代码")
    email = serializers.CharField(help_text="注册邮箱")

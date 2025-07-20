from rest_framework import serializers

from JobRecServer.apps.student.models import Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"
        depth = 2  # 深度


class ClickStudentSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(help_text="学生id")
    job_id = serializers.IntegerField(help_text="职位id")


class ChangePasswordSerializer(serializers.Serializer):
    old = serializers.CharField(help_text="旧密码")
    new = serializers.CharField(help_text="新密码")


class RecommendStudentSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="职位id")


class SearchStudentSerializer(serializers.Serializer):
    DEPARTMENT = serializers.CharField(help_text="学院", required=False)
    ZYFX = serializers.CharField(help_text="专业方向", required=False)
    XXXSMC = serializers.CharField(help_text="学习形式名称", required=False)
    key = serializers.CharField(help_text="搜索关键词", required=False)

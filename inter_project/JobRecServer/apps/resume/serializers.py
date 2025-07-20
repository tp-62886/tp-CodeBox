from rest_framework import serializers

from JobRecServer.apps.resume.models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = "__all__"
        depth = 2  # 深度


class UpdateResumeSerializer(serializers.Serializer):
    personalAdvantage = serializers.CharField(help_text="个人优势")
    schoolExperience = serializers.CharField(help_text="学校经历")
    expectedPositions = serializers.CharField(help_text="期望职位")

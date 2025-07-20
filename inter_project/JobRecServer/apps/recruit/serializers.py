from rest_framework import serializers

from JobRecServer.apps.recruit.models import Recruit


class RecruitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruit
        fields = "__all__"
        depth = 2


class SendResumeSerializer(serializers.Serializer):
    job_id = serializers.CharField(help_text="职位id", required=False)

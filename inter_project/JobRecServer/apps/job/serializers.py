from rest_framework import serializers

from JobRecServer.apps.job.models import Job


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = "__all__"

    # 指定日期格式
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['create_time'].format = "%Y-%m-%d"


class ClickJobSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="职位id")


class SearchJobSerializer(serializers.Serializer):
    GZZWLBMC = serializers.CharField(help_text="职位名", required=False)


class SaveJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        exclude = ('DWZZJGDM', 'company')

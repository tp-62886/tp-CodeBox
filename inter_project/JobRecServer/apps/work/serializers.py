from rest_framework import serializers

from JobRecServer.apps.work.models import Work


class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = "__all__"


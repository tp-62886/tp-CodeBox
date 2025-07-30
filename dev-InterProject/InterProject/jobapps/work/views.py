from django.forms import model_to_dict
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from jobapps.work.models import Work
from jobapps.work.serializers import WorkSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q


class WorkViewSet(viewsets.ModelViewSet):
    queryset = Work.objects.all()
    serializer_class = WorkSerializer
    schema = AutoSchema()
    # ordering = 'id'

    @method_decorator(cache_page(60 * 15), name='workList')  # 缓存list方法15分钟
    def list(self, request, *args, **kwargs):
        """
        获取职位列表
        """
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        新增职位
        """
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        获取职位详情
        """
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        更新职位信息
        """
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        部分更新职位信息
        """
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        删除职位信息
        """
        return super().destroy(request, *args, **kwargs)

    # @action(detail=False, methods=['GET'])
    # def hotList(self, request):
    #     """
    #     获取热门职位列表
    #     """
    #     # 随机获取职位
    #     jobs = list(Work.objects.filter(Q(job_name__len__lte=10)).order_by('?')[:9])
    #     data = []
    #     for job in jobs:
    #         data.append(model_to_dict(job))
    #     return Response(status=status.HTTP_200_OK, data=data)

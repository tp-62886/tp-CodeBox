from django.forms import model_to_dict
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action

from .models import Resume
from .serializers import ResumeSerializer
from ..student.models import Student


class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer

    def list(self, request, *args, **kwargs):
        """
        获取简历列表
        """
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        新增简历
        """
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        获取简历详情
        """
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        更新学生简历
        """
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        部分更新学生简历
        """
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        删除学生简历
        """
        return super().destroy(request, *args, **kwargs)

    # @action(detail=False, methods=['GET'])
    # def getResume(self, request):
    #     """
    #     获取当前登录学生的简历
    #     若没有则创建
    #     """
    #     user = request.user
    #     student = Student.objects.filter(user=user).first()
    #     resume = Resume.objects.filter(student=student).first()
    #     if not resume:  # 若没有则创建
    #         Resume.objects.create(student=student)
    #         resume = Resume.objects.filter(student=student).first()
    #         return Response(status=status.HTTP_200_OK, data=model_to_dict(resume))
    #     else:  # 若有直接返回结果
    #         return Response(status=status.HTTP_200_OK, data=model_to_dict(resume))

    @action(detail=False, methods=['GET'])
    def getResumeById(self, request):
        """
        根据学生id获取学生简历
        若没有则创建
        """
        student_id = request.GET.get('id')
        student = Student.objects.filter(id=student_id).first()
        resume = Resume.objects.filter(student=student).first()
        if not resume:  # 若没有则创建
            Resume.objects.create(student=student)
            resume = Resume.objects.filter(student=student).first()
            return Response(status=status.HTTP_200_OK, data=model_to_dict(resume))
        else:  # 若有直接返回结果
            return Response(status=status.HTTP_200_OK, data=model_to_dict(resume))

    # @action(detail=False, methods=['POST'], serializer_class=ResumeSerializer)
    # def updateResume(self, request):
    #     """
    #     更新简历信息
    #     """
    #     user = request.user
    #     student = Student.objects.filter(user=user).first()
    #     resume = Resume.objects.filter(student=student).first()

    #     serializer = ResumeSerializer(instance=resume, data=request.data)
    #     serializer.is_valid(raise_exception=True)  # 进行数据验证,未通过则抛出异常
    #     serializer.save()

    #     return Response(serializer.data, status=status.HTTP_200_OK)

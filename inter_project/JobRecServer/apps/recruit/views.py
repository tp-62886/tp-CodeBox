from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from JobRecServer.apps.company.models import Company
from JobRecServer.apps.job.models import Job
from JobRecServer.apps.recruit.models import Recruit
from JobRecServer.apps.recruit.serializers import RecruitSerializer, SendResumeSerializer
from JobRecServer.apps.student.models import Student


class RecruitViewSet(viewsets.ModelViewSet):
    queryset = Recruit.objects.all()
    serializer_class = RecruitSerializer
    schema = AutoSchema()

    # ordering = 'id'

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    # @action(detail=False, methods=['POST'], serializer_class=SendResumeSerializer)
    # def send(self, request):
    #     """
    #     学生向某个职位投递简历
    #     """
    #     serializer = SendResumeSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)  # 进行数据验证,未通过则抛出异常
    #     # 获取当前登录的用户
    #     user = request.user
    #     # 根据用户id找到对应的学生
    #     student = Student.objects.filter(user_id=user.id).first()
    #     # 根据职位编号找到对应的职位
    #     job = Job.objects.filter(id=serializer.data['job_id']).first()
    #     # 如果没有则新增到数据库
    #     flag = Recruit.objects.filter(student=student.id, job=job.id).first()
    #     if flag is not None:
    #         return Response(status=status.HTTP_200_OK)
    #     Recruit.objects.create(student=student, job=job, status=0)
    #     return Response(status=status.HTTP_200_OK)

    # @action(detail=False, methods=['POST'], serializer_class=SendResumeSerializer)
    # def changeStatus(self, request):
    #     """
    #     公司阅读简历后,修改简历状态
    #     """
    #     serializer = SendResumeSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)  # 进行数据验证,未通过则抛出异常
    #     recruit = Recruit.objects.filter(id=serializer.data['job_id']).first()
    #     recruit.status = 1
    #     recruit.save()
    #     return Response(status=status.HTTP_200_OK)

    # @action(detail=False, methods=['GET'])
    # def getStudent(self, request):
    #     """
    #     学生查看自己投递的简历
    #     """
    #     user = request.user
    #     student = Student.objects.filter(user_id=user.id).first()
    #     recruits = Recruit.objects.filter(student_id=student.id)

    #     serializer = RecruitSerializer(recruits, many=True)
    #     return Response(status=status.HTTP_200_OK, data=serializer.data)

    # @action(detail=False, methods=['GET'])
    # def getCompany(self, request):
    #     """
    #     公司查看投递给自己的简历
    #     """
    #     user = request.user
    #     company = Company.objects.filter(user_id=user.id).first()
    #     if company is None:
    #         return Response(status=status.HTTP_200_OK, data=[])
    #     # 获取该公司创建的所有职位
    #     jobs = Job.objects.filter(company=company)
    #     # 获取所有投递到这些职位的简历
    #     recruits = Recruit.objects.filter(job__in=jobs)
    #     serializer = RecruitSerializer(recruits, many=True)

    #     return Response(status=status.HTTP_200_OK, data=serializer.data)

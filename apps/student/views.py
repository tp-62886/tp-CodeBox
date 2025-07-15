import json
import random

import pandas as pd
from django.forms import model_to_dict
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import Student
from .serializers import StudentSerializer, ChangePasswordSerializer, RecommendStudentSerializer, \
    ClickStudentSerializer, SearchStudentSerializer
from ..job.models import Job
from ..middle.models import ClickStudent
from ..user.models import User
from django.db.models import Q
import re
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator


def extract_majors(major_string):
    # 定义正则表达式模式，匹配【本科】、【硕士】、【博士】开头的专业，或者没有前缀的专业
    pattern = r'【(?:本科|硕士|博士)】[^\s,]+|[^【,]+(?=\s*，|\s*$)'

    # 使用正则表达式查找所有匹配项
    matches = re.findall(pattern, major_string)

    # 去除前缀（【本科】、【硕士】、【博士】）并清理空白字符
    majors = []
    for match in matches:
        # 匹配【本科】、【硕士】、【博士】前缀
        if match.startswith('【'):
            major = re.sub(r'【(?:本科|硕士|博士)】', '', match).strip()
        else:
            major = match.strip()
        majors.append(major)

    return majors


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5  # 每页显示的默认条数
    page_size_query_param = 'page_size'  # URL中每页数量参数
    max_page_size = 100  # 支持的最大每页数量


class StudentViewSet(viewsets.ModelViewSet):
    authentication_classes = []
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    @method_decorator(cache_page(60 * 15), name='studentList')  # 缓存list方法15分钟
    def list(self, request, *args, **kwargs):
        """
        获取学生列表
        """
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        新增学生
        """
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        获取学生详情
        """
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        更新学生信息
        """
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        部分更新学生信息
        """
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        删除学生
        """
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['GET'])
    def createUsers(self, request):
        """
        为所有学生批量创建账号
        """
        students = Student.objects.all()
        for student in students:  # 遍历所有学生
            username = student.SID
            password = '123456'  # 密码默认设为123456
            if not User.objects.filter(username=username).exists():  # 若用户不存在
                user = User.objects.create_user(username=username, password=password)
                user.save()
                # 进行外键关联
                student.user = user
                student.save()

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], serializer_class=ChangePasswordSerializer)
    def changePassword(self, request):
        """
        修改密码
        """
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 进行数据验证,未通过则抛出异常
        old_password = serializer.validated_data['old']
        new_password = serializer.validated_data['new']
        # 获取当前登录的用户
        user = request.user
        # 修改密码
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], serializer_class=RecommendStudentSerializer)
    def recommend(self, request):
        """
        给职位推荐候选人
        """
        serializer = RecommendStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 对应的职位
        job = Job.objects.get(id=serializer.validated_data['id'])
        # 职位编号
        input_id = job.DWZZJGDM

        # 解析 major 字段，获得所需专业列表
        job_major_list = extract_majors(job.major)
        # print(job_major_list)
        # 存储推荐的学生
        recommend_students = []

        # 对每个所需专业，匹配最多 3 个相符的学生
        for major_item in job_major_list:
            # 查询该专业的学生，按照一定条件排序（例如成绩、面试表现等），获取最多 3 个
            students = Student.objects.filter(MAJOR=major_item)[:3]
            if students is not None:
                recommend_students.extend(students)

        # 如果推荐的学生总数超过 15，截取前 15 个
        if len(recommend_students) > 15:
            recommend_students = recommend_students[:15]

        data = []
        for temp in recommend_students:
            serializer = StudentSerializer(temp)
            data.append(serializer.data)
        return Response(status=status.HTTP_200_OK, data=data)

        # 调用模型进行推荐
        # try:
        #     recommendations = recommender.recommend_users_for_job(input_id, num_recommendations=5)
        # except SyntaxError:
        #     recommendations = None
        #
        # user_ids = []
        #
        # if recommendations is not None:
        #     for recommendation in recommendations:
        #         userid = recommendation[0]
        #         user_ids.append(int(userid))
        # else:
        #     students = Student.objects.all()
        #     random_students = random.sample(list(students), 5)
        #     for student in random_students:
        #         serializer = StudentSerializer(student)
        #         user_ids.append(serializer.data.SID)

        # user_ids = []
        #
        # users_list = []

        # students = Student.objects.all()
        # random_students = random.sample(list(students), 5)
        # for student in random_students:
        #     serializer = StudentSerializer(student)
        #     users_list.append(serializer.data)
        # return Response(status=status.HTTP_200_OK, data=users_list)

        # if len(user_ids) == 0:  # 调用冷启动模型
        #     # 读取 xdu_dataset_user.xlsx
        #     job_df = pd.read_excel('data/xdu/xdu_dataset_job.xlsx')
        #
        #     # 根据 SID 获取 MAJOR 字段值
        #     job_row = job_df[job_df['DWZZJGDM'] == input_id]
        #
        #     # 获取职位的所属行业
        #     DWHYMC = job_row['DWHYMC'].values[0]
        #
        #     # 读取 major_trans.txt
        #     with open('data/xdu/DWHYMC_trans.txt', 'r', encoding='utf-8') as f:
        #         DWHYMC_trans = dict(line.strip().split(' ') for line in f)
        #
        #     # 获取映射后的 MAJOR 值
        #     mapped_DWHYMC = DWHYMC_trans.get(DWHYMC)
        #
        #     # 读取 recommend_result 文件
        #     with open('data/xdu/recommend_result_com', 'r') as f:
        #         recommend_result = json.load(f)
        #
        #     # 获取推荐列表
        #     recommend_list = recommend_result.get(mapped_DWHYMC)
        #
        #     # 取推荐列表长度和10的较小值
        #     top_n = min(len(recommend_list), 10)
        #     top_recommendations = recommend_list[:top_n]
        #
        #     # 读取 xdu_dataset_job.xlsx
        #     user_df = pd.read_excel('data/xdu/xdu_dataset_user.xlsx')
        #
        #     # 打印推荐结果
        #     for rec in top_recommendations:
        #         user_dict = user_df[user_df['SID'] == int(rec)]
        #
        #         users_list.append(user_dict)
        #
        # else:  # 调用推荐模型
        #     for user_id in user_ids:
        #         student = Student.objects.filter(SID=user_id).first()
        #         if student:
        #             serializer = StudentSerializer(student)
        #             users_list.append(serializer.data)
        #
        # return Response(status=status.HTTP_200_OK, data=users_list)

    @action(detail=False, methods=['POST'], serializer_class=ClickStudentSerializer)
    def clickStudent(self, request):
        """
        企业浏览学生信息
        """
        serializer = ClickStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 进行数据验证,未通过则抛出异常
        # 根据学生id找到对应的学生
        student = Student.objects.filter(id=serializer.data['student_id']).first()
        # 根据职位编号找到对应的职位
        job = Job.objects.filter(id=serializer.data['job_id']).first()
        # 新增到数据库
        click = ClickStudent.objects
        click.create(SID=student, DWZZJGDM=job, satisfied=1)
        return Response(status=status.HTTP_200_OK)

    # @action(detail=False, methods=['POST'], serializer_class=SearchStudentSerializer)
    # def searchStudent(self, request):
    #     """
    #     根据关键词或者条件检索学生信息
    #     """
    #     # 对传入数据进行序列化
    #     serializer = SearchStudentSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     # 从序列化器数据中获取查询条件
    #     department = serializer.data['DEPARTMENT']
    #     zyfx = serializer.data['ZYFX']
    #     xxxsmc = serializer.data['XXXSMC']
    #     # 关键词
    #     key = serializer.data['key']
    #     # 构建查询条件
    #     filter_conditions = Q()
    #     if department != '0':
    #         filter_conditions &= Q(DEPARTMENT=department)
    #     if zyfx != '0':
    #         filter_conditions &= Q(ZYFX=zyfx)
    #     if xxxsmc != '0':
    #         filter_conditions &= Q(XXXSMC=xxxsmc)
    #     # 根据关键词key从department、zyfx、xxxsmc三个字段中查询
    #     if key:
    #         filter_conditions &= (
    #                 Q(DEPARTMENT__contains=key) |
    #                 Q(ZYFX__contains=key) |
    #                 Q(XXXSMC__contains=key)
    #         )
    #     # 从数据库中查询数据
    #     student_queryset = Student.objects.filter(filter_conditions)[:5]
    #     students = [model_to_dict(student) for student in student_queryset]
    #     return Response(status=status.HTTP_200_OK, data=students)

    @action(detail=False, methods=['POST'], serializer_class=SearchStudentSerializer)
    def searchStudent(self, request):
        """
        根据关键词或者条件检索学生信息（分页查询）
        """
        # 对传入数据进行序列化
        serializer = SearchStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 从序列化器数据中获取查询条件
        department = serializer.data['DEPARTMENT']
        zyfx = serializer.data['ZYFX']
        xxxsmc = serializer.data['XXXSMC']
        # 关键词
        key = serializer.data['key']
        # 构建查询条件
        filter_conditions = Q()
        if department != '0':
            filter_conditions &= Q(DEPARTMENT=department)
        if zyfx != '0':
            filter_conditions &= Q(ZYFX=zyfx)
        if xxxsmc != '0':
            filter_conditions &= Q(XXXSMC=xxxsmc)
        # 根据关键词key从department、zyfx、xxxsmc三个字段中查询
        if key != '0':
            filter_conditions &= (
                    Q(DEPARTMENT__contains=key) |
                    Q(ZYFX__contains=key) |
                    Q(XXXSMC__contains=key)
            )
            student_queryset = Student.objects.filter(filter_conditions)
        else:
            student_queryset = Student.objects.all()

        # 分页处理
        paginator = StandardResultsSetPagination()
        paginated_queryset = paginator.paginate_queryset(student_queryset, request)
        students = [model_to_dict(student) for student in paginated_queryset]

        # 返回分页后的数据
        return paginator.get_paginated_response(students)

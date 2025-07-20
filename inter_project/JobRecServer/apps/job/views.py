import datetime
import json
import random
from operator import itemgetter

import numpy as np
import pandas as pd
from django.db.models import Q
from django.db.models.functions import Length
from django.forms import model_to_dict
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from JobRecServer.JobRec.DPGNN.model.prediction import JobRecommender
from JobRecServer.apps.middle.models import ClickJob, StarJob
from .models import Job
from .serializers import JobSerializer, ClickJobSerializer, SearchJobSerializer, SaveJobSerializer
from ..company.models import Company
from ..resume.models import Resume
from ..student.models import Student


# 读取保存好的模型
# recommender = JobRecommender(config_file='xdu',
#                              checkpoint_path='JobRec/DPGNN/model/saved/DPGNN-Sep-10-2024_23-29-08.pth')


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'  # 查询参数
    max_page_size = 10


# todo 根据当前登录学生的期望职位进行推荐
def recommendByExpectedPositions(student):
    resume = Resume.objects.filter(student_id=student.id).first()
    if resume is None:
        return []
    degree = student.XLMC  # 获取学生学历
    result = []
    if resume.expectedPositions is None:
        return []
    expectedPositions = resume.expectedPositions.split(',')
    for key in expectedPositions:
        # 根据传入的key（职位名称）查找最接近的职位
        # 使用Q对象和contains进行模糊查询，获取与key最接近的职位
        if degree == "本科生":
            jobs = Job.objects.filter(
                Q(GZZWLBMC__icontains=key) | Q(desc__icontains=key), degree__icontains="本科"
            ).distinct()
            # print("给本科生推荐")
        else:
            jobs = Job.objects.filter(
                Q(GZZWLBMC__icontains=key) | Q(desc__icontains=key)
            ).distinct()
            # print("给研究生推荐")
        jobs_list = list(jobs)
        # 如果不足5个，从其他职位中随机选择剩余的职位
        if len(jobs_list) < 3:
            remaining_count = 5 - len(jobs_list)
            if degree == "本科生":
                other_jobs = Job.objects.exclude(
                    Q(major__contains=student.MAJOR) | ~Q(major__contains="本科")
                )
            else:
                other_jobs = Job.objects.exclude(major__contains=student.MAJOR)
            other_jobs_list = list(other_jobs)
            if other_jobs_list:
                random_other_jobs = random.sample(other_jobs_list, min(remaining_count, len(other_jobs_list)))
                jobs_list.extend(random_other_jobs)  # 将随机选择的其他职位添加到列表中
        # 随机打乱最终的职位列表
        # random.shuffle(jobs_list)
        final_jobs = jobs_list[:3]
        for job in final_jobs:
            result.append(job)

    return result[:10]


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    schema = AutoSchema()
    pagination_class = StandardResultsSetPagination  # 自定义分页类

    @method_decorator(cache_page(60 * 15), name='jobList')  # 缓存list方法15分钟
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
        企业删除职位信息
        """
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['GET'])
    def recommend(self, request):
        """
        给学生推荐职位
        判断有无交互记录
        若没有，则调用冷启动模型
        若有，则调用使用交互记录的模型
        """
        # 获取当前登录的学生学号
        user = request.user
        student = Student.objects.filter(user_id=user.id).first()
        sid = student.SID
        major = student.MAJOR
        print(f"学生学号: {sid}, 专业: {major}")
        # 根据学生专业筛选职位
        jobs = Job.objects.filter(major__contains=major)
        jobs_list = list(jobs)
        # 如果不足5个，从其他职位中随机选择剩余的职位
        if len(jobs_list) < 5:
            remaining_count = 5 - len(jobs_list)
            other_jobs = Job.objects.exclude(major__contains=major)  # 获取不符合专业要求的职位
            other_jobs_list = list(other_jobs)
            if other_jobs_list:
                random_other_jobs = random.sample(other_jobs_list, min(remaining_count, len(other_jobs_list)))
                jobs_list.extend(random_other_jobs)  # 将随机选择的其他职位添加到列表中

        # 随机打乱最终的职位列表
        random.shuffle(jobs_list)
        final_jobs = jobs_list[:5]  # 确保最终返回5个职位

        # 序列化职位数据
        serialized_jobs = [JobSerializer(job).data for job in final_jobs]

        return Response(status=status.HTTP_200_OK, data=serialized_jobs)

        # jobs_list = []
        # jobs = Job.objects.all()
        # random_jobs = random.sample(list(jobs), 5)
        # for job in random_jobs:
        #     serializer = JobSerializer(job)
        #     jobs_list.append(serializer.data)
        # return Response(status=status.HTTP_200_OK, data=jobs_list)

        # # 调用模型进行推荐
        # recommendations = recommender.recommend_jobs_for_user(sid, num_recommendations=5)
        # job_ids = []
        # for recommendation in recommendations:
        #     jobid = recommendation[0]
        #     job_ids.append(jobid)
        #
        # # 定义一个用来保存工作对象的列表
        # jobs_list = []
        #
        # if len(job_ids) == 0:  # 调用冷启动模型
        #     # 读取 xdu_dataset_user.xlsx
        #     user_df = pd.read_excel('data/xdu/xdu_dataset_user.xlsx')
        #
        #     # 根据 SID 获取 MAJOR 字段值
        #     user_row = user_df[user_df['SID'] == sid]
        #
        #     # 若没有找到学生学号则随机推荐5个
        #     if user_row is None:
        #         jobs = Job.objects.all()[:5]
        #         data = []
        #         for job in jobs:
        #             data.append(model_to_dict(job))
        #         return Response(status=status.HTTP_200_OK, data=data)
        #
        #     major = user_row['MAJOR'].values[0]
        #
        #     # 读取 major_trans.txt
        #     with open('data/xdu/major_trans.txt', 'r', encoding='utf-8') as f:
        #         major_trans = dict(line.strip().split(' ') for line in f)
        #
        #     # 获取映射后的 MAJOR 值
        #     mapped_major = major_trans.get(major)
        #
        #     # 读取 recommend_result 文件
        #     with open('data/xdu/recommend_job_result', 'r') as f:
        #         recommend_result = json.load(f)
        #
        #     # 获取推荐列表
        #     recommend_list = recommend_result.get(mapped_major)
        #
        #     # 取推荐列表长度和10的较小值
        #     top_n = min(len(recommend_list), 5)
        #     top_recommendations = recommend_list[:top_n]
        #
        #     # 读取 xdu_dataset_job.xlsx
        #     job_df = pd.read_excel('data/xdu/xdu_dataset_job.xlsx')
        #
        #     # 打印推荐结果
        #     for rec in top_recommendations:
        #         job_dict = job_df[job_df['DWZZJGDM'] == rec]
        #
        #         jobs_list.append(job_dict)
        #
        # else:  # 调用推荐模型
        #     # for job_id in job_ids:
        #     #     job = Job.objects.filter(DWZZJGDM=job_id).first()
        #     #     if job:
        #     #         serializer = JobSerializer(job)
        #     #         jobs_list.append(serializer.data)
        #     jobs = Job.objects.all()
        #     random_jobs = random.sample(list(jobs), 5)
        #     for job in random_jobs:
        #         serializer = JobSerializer(job)
        #         jobs_list.append(serializer.data)
        #
        # return Response(status=status.HTTP_200_OK, data=jobs_list)

    @action(detail=False, methods=['GET'])
    def coldRecommend(self, request):
        """
        冷启动推荐
        """
        user = request.user
        student = Student.objects.get(user_id=user.id)
        sid = student.SID
        # sid = "24181214457"
        print('学生学号:', sid)

        # 定义一个用来保存工作对象的列表
        jobs_list = []

        # 读取 xdu_dataset_user.xlsx
        user_df = pd.read_excel('data/xdu/xdu_dataset_user.xlsx')

        # 根据 SID 获取 MAJOR 字段值
        user_row = user_df[user_df['SID'] == sid]

        major = user_row['MAJOR'].values[0]

        # major = student.MAJOR

        # 读取 major_trans.txt
        with open('data/xdu/major_trans.txt', 'r', encoding='utf-8') as f:
            major_trans = dict(line.strip().split(' ') for line in f)

        # 获取映射后的 MAJOR 值
        mapped_major = major_trans.get(major)

        # 读取 recommend_result 文件
        with open('data/xdu/recommend_result', 'r') as f:
            recommend_result = json.load(f)

        # 获取推荐列表
        recommend_list = recommend_result.get(mapped_major)
        # print(recommend_list)

        if recommend_list is None:
            recommend_list = []

        random.shuffle(recommend_list)

        # 取推荐列表长度和15的较小值
        top_n = min(len(recommend_list), 15)
        print("模型输出个数", top_n)
        top_recommendations = recommend_list[:top_n]

        # 获取推荐结果
        for job_id in top_recommendations:
            # 过滤 2024 年之后的职位
            job = Job.objects.filter(DWZZJGDM=job_id, create_time__gte=datetime.date(2024, 1, 1)).exclude(major__contains='博士').first()
            if job:
                serializer = JobSerializer(job)
                jobs_list.append(serializer.data)

        # 根据学生的期望招聘进行推荐
        # result = recommendByExpectedPositions(student)
        # for job in result:
        #     if job:
        #         serializer = JobSerializer(job)
        #         jobs_list.append(serializer.data)

        # 推荐数量小于20
        if len(jobs_list) < 20:
            less = 20 - len(jobs_list)
            print('less:', less)
            print('major:', student.MAJOR)
            # 过滤 2024 年之后的职位
            jobs = Job.objects.filter(major__contains=student.MAJOR,
                                      create_time__gte=datetime.date(2024, 1, 1)).exclude(major__contains='博士')[:less]

            for job in jobs:
                serializer = JobSerializer(job)
                jobs_list.append(serializer.data)

        # 使用随机职位填充
        if len(jobs_list) < 20:
            less = 20 - len(jobs_list)
            jobs = Job.objects.filter(create_time__gte=datetime.date(2024, 1, 1)).exclude(major__contains='博士')
            random_jobs = random.sample(list(jobs), less)
            for student in random_jobs:
                serializer = JobSerializer(student)
                jobs_list.append(serializer.data)

        # 根据 create_time 降序排序
        jobs_list = sorted(jobs_list, key=itemgetter('create_time'), reverse=True)[:20]
        # print("推荐总个数", len(jobs_list))
        return Response(status=status.HTTP_200_OK, data=jobs_list)

    @action(detail=False, methods=['POST'], serializer_class=ClickJobSerializer)
    def clickJob(self, request):
        """
        学生浏览职位后添加交互记录
        """
        serializer = ClickJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 进行数据验证,未通过则抛出异常
        # 获取当前登录的用户
        user = request.user
        # 根据用户id找到对应的学生
        student = Student.objects.filter(user_id=user.id).first()
        if student is None:
            return Response(status=status.HTTP_200_OK)
        # 根据职位编号找到对应的职位
        job = Job.objects.filter(id=serializer.data['id']).first()
        # 如果没有则新增到数据库
        ClickJob.objects.update_or_create(student=student, job=job)
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def clickList(self, request):
        """
        查看浏览职位列表
        """
        user = request.user
        # 根据用户id找到对应的学生
        student = Student.objects.filter(user_id=user.id).first()
        # queryset = ClickJob.objects.filter(SID=student.SID)
        queryset = ClickJob.objects.filter(student_id=student.id)

        data = []
        # 使用set进行去重
        seen = set()
        for e in queryset:
            job = Job.objects.filter(DWZZJGDM=e.DWZZJGDM.DWZZJGDM).first()
            if job not in seen:
                seen.add(job)
                data.append(model_to_dict(job))
        return Response(status=status.HTTP_200_OK, data=data)

    # @action(detail=False, methods=['POST'], serializer_class=ClickJobSerializer)
    # def starJob(self, request):
    #     """
    #     学生收藏职位
    #     """
    #     serializer = ClickJobSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)  # 进行数据验证,未通过则抛出异常
    #     # 获取当前登录的用户
    #     user = request.user
    #     # 根据用户id找到对应的学生
    #     student = Student.objects.filter(user_id=user.id).first()
    #     # 根据职位编号找到对应的职位
    #     job = Job.objects.filter(id=serializer.data['id']).first()
    #     # 新增到数据库
    #     star = StarJob.objects
    #     star.create(SID=student, DWZZJGDM=job, satisfied=1)
    #     return Response(status=status.HTTP_200_OK)

    # @action(detail=False, methods=['GET'])
    # def starList(self, request):
    #     """
    #     查看收藏职位列表
    #     """
    #     user = request.user
    #     # 根据用户id找到对应的学生
    #     student = Student.objects.filter(user_id=user.id).first()
    #     # queryset = StarJob.objects.filter(SID=student.SID)
    #     queryset = StarJob.objects.filter(student_id=student.id)
    #     data = []
    #     # 使用set进行去重
    #     seen = set()
    #     for e in queryset:
    #         job = Job.objects.filter(DWZZJGDM=e.DWZZJGDM.DWZZJGDM).first()
    #         if job not in seen:
    #             seen.add(job)
    #             data.append(model_to_dict(job))
    #     return Response(status=status.HTTP_200_OK, data=data)

    # @action(detail=False, methods=['POST'], serializer_class=SearchJobSerializer)
    # def searchJob(self, request):
    #     """
    #     根据关键词搜索职位信息
    #     """
    #     # 对传入数据进行序列化
    #     serializer = SearchJobSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     # 获取职位名称
    #     GZZWLBMC = serializer.data['GZZWLBMC']
    #     # 构建查询条件
    #     filter_conditions = Q()
    #     filter_conditions &= Q(GZZWLBMC__contains=GZZWLBMC)
    #     # 从数据库中查询数据
    #     job_queryset = Job.objects.filter(filter_conditions)[:10]
    #     jobs = [model_to_dict(student) for student in job_queryset]
    #     return Response(status=status.HTTP_200_OK, data=jobs)

    # @action(detail=False, methods=['POST'], serializer_class=SaveJobSerializer)
    # def save(self, request):
    #     """
    #     企业新建职位
    #     """
    #     user = request.user
    #     if not user.is_authenticated:
    #         return Response(status=status.HTTP_200_OK, data=None)
    #     company = Company.objects.filter(user_id=user.id).first()

    #     serializer = SaveJobSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)

    #     job = Job.objects.create(company=company, **serializer.validated_data)
    #     job.DWZZJGDM = str(job.id)
    #     job.save()
    #     return Response(status=status.HTTP_200_OK, data=model_to_dict(job))

    @action(detail=False, methods=['GET'])
    def myJob(self, request):
        """
        获取当前登录企业创建的所有职位
        根据企业编号获取
        """
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_200_OK, data=None)
        # print(user.id)
        company = Company.objects.filter(user_id=user.id).first()
        if company is None:
            return Response(status=status.HTTP_200_OK, data=None)
        # print(company.id)

        jobs = Job.objects.filter(COMPANYID=company.COMPANYID)
        # print(jobs)

        data = []
        for job in jobs:
            data.append(model_to_dict(job))
        return Response(status=status.HTTP_200_OK, data=data)

    @action(detail=False, methods=['GET'])
    def recommendJob(self, request):  # TODO 给学生推荐职位
        """
        给学生推荐职位
        """
        # 获取前端传入的搜索关键词
        key = request.GET.get('key')
        # key = '研发类岗位'
        # 获取学生的基本信息
        user = request.user
        student = Student.objects.filter(user_id=user.id).first()
        print(f"学生学号: {student.SID}, 专业: {student.MAJOR}")
        if key is None:
            # 根据学生专业筛选职位
            jobs = Job.objects.filter(major__contains=student.MAJOR)
            jobs_list = list(jobs)
            # 如果不足5个，从其他职位中随机选择剩余的职位
            if len(jobs_list) < 5:
                remaining_count = 5 - len(jobs_list)
                other_jobs = Job.objects.exclude(major__contains=student.MAJOR)  # 获取不符合专业要求的职位
                other_jobs_list = list(other_jobs)
                if other_jobs_list:
                    random_other_jobs = random.sample(other_jobs_list, min(remaining_count, len(other_jobs_list)))
                    jobs_list.extend(random_other_jobs)  # 将随机选择的其他职位添加到列表中
            # 随机打乱最终的职位列表
            # random.shuffle(jobs_list)
            final_jobs = jobs_list[:5]  # 确保最终返回5个职位
            # 序列化职位数据
            serialized_jobs = [JobSerializer(job).data for job in final_jobs]
            return Response(status=status.HTTP_200_OK, data=serialized_jobs)
        else:
            # 根据传入的key（职位名称）查找最接近的职位
            # 使用Q对象和contains进行模糊查询，获取与key最接近的职位
            jobs = Job.objects.filter(
                Q(GZZWLBMC__icontains=key) | Q(desc__icontains=key)
            ).distinct()
            jobs_list = list(jobs)
            # 如果不足5个，从其他职位中随机选择剩余的职位
            if len(jobs_list) < 5:
                remaining_count = 5 - len(jobs_list)
                other_jobs = Job.objects.exclude(major__contains=student.MAJOR)  # 获取不符合专业要求的职位
                other_jobs_list = list(other_jobs)
                if other_jobs_list:
                    random_other_jobs = random.sample(other_jobs_list, min(remaining_count, len(other_jobs_list)))
                    jobs_list.extend(random_other_jobs)  # 将随机选择的其他职位添加到列表中
            # 随机打乱最终的职位列表
            # random.shuffle(jobs_list)
            final_jobs = jobs_list[:5]  # 确保最终返回5个职位
            # 序列化职位数据
            serialized_jobs = [JobSerializer(job).data for job in final_jobs]
            return Response(status=status.HTTP_200_OK, data=serialized_jobs)

    # @action(detail=False, methods=['GET'])
    # def recommend_jobs(self, request):  # 相似度推荐算法
    #     user = request.user
    #     student = Student.objects.filter(user_id=user.id).first()
    #     student_id = student.id

    #     top_n = 5

    #     viewed_jobs = ClickJob.objects.filter(student_id=student_id).values_list('job', flat=True)
    #     viewed_job_descriptions = Job.objects.filter(id__in=viewed_jobs).values_list('desc', flat=True)

    #     all_jobs = list(Job.objects.all())
    #     all_job_descriptions = [job.desc for job in all_jobs]

    #     vectorizer = TfidfVectorizer()
    #     viewed_job_vectors = vectorizer.fit_transform(viewed_job_descriptions)
    #     all_job_vectors = vectorizer.transform(all_job_descriptions)

    #     similarities = cosine_similarity(viewed_job_vectors, all_job_vectors)
    #     average_similarities = np.mean(similarities, axis=0)

    #     top_job_indices = np.argsort(average_similarities)[-top_n:][::-1]
    #     recommended_jobs = [all_jobs[int(i)] for i in top_job_indices if all_jobs[int(i)].id not in viewed_jobs]

    #     serialized_jobs = [JobSerializer(job).data for job in recommended_jobs]
    #     return Response(status=status.HTTP_200_OK, data=serialized_jobs)
    
    @action(detail=False, methods=['GET'])
    def recommend_jobs(self, request):  # 相似度推荐算法
        user = request.user
        student = Student.objects.filter(user_id=user.id).first()
    
        if not student:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

    # 1. 获取用户浏览过的职位ID（去重）
        viewed_jobs = ClickJob.objects.filter(
            student_id=student.id
        ).values_list('job', flat=True).distinct()

    # 2. 获取有效的职位描述（排除空值）
        valid_descriptions = []
        for desc in Job.objects.filter(id__in=viewed_jobs)\
                         .exclude(desc__isnull=True)\
                         .exclude(desc__exact='')\
                         .values_list('desc', flat=True):
            if desc and str(desc).strip():
                valid_descriptions.append(desc)

    # 3. 如果没有浏览记录或有效描述，返回基于专业的推荐
        if not valid_descriptions:
            major_jobs = Job.objects.filter(
                major__contains=student.MAJOR
            ).order_by('?')[:5]  # 随机取5个专业相关职位
            serializer = JobSerializer(major_jobs, many=True)
            return Response(serializer.data)

    # 4. 文本向量化（增加容错处理）
        try:
            vectorizer = TfidfVectorizer(
                min_df=1,  # 至少出现1次
                stop_words=None,  # 禁用默认停用词
                token_pattern=r'(?u)\b\w+\b'  # 包含单字符词
            )
            viewed_job_vectors = vectorizer.fit_transform(valid_descriptions)
        
        # 获取所有职位描述（同样过滤空值）
            all_descriptions = []
            all_jobs = list(Job.objects.all())
            for desc in Job.objects.all()\
                                 .exclude(desc__isnull=True)\
                                 .exclude(desc__exact='')\
                                 .values_list('desc', flat=True):
                if desc and str(desc).strip():
                    all_descriptions.append(desc)
        
            all_job_vectors = vectorizer.transform(all_descriptions)

        # 5. 计算相似度
            similarities = cosine_similarity(viewed_job_vectors, all_job_vectors)
            average_similarities = np.mean(similarities, axis=0)
        
        # 6. 获取推荐结果（排除已浏览的）
            top_indices = np.argsort(average_similarities)[-5:][::-1]  # 取Top5
            recommended_jobs = []
            for i in top_indices:
                if all_jobs[i].id not in viewed_jobs:
                    recommended_jobs.append(all_jobs[i])
                    if len(recommended_jobs) >= 5:
                        break
        
            serializer = JobSerializer(recommended_jobs, many=True)
            return Response(serializer.data)

        except ValueError as e:
        # 向量化失败时返回随机推荐
            random_jobs = Job.objects.order_by('?')[:5]
            serializer = JobSerializer(random_jobs, many=True)
            return Response(serializer.data)

    # @action(detail=False, methods=['GET'])
    # def hotList(self, request):
    #     """
    #     获取热门职位列表
    #     """
    #     jobs = list(Job.objects.annotate(length=Length('GZZWLBMC')).filter(length__lte=10).order_by('-create_time')[:9])

    #     data = []
    #     for job in jobs:
    #         data.append(model_to_dict(job))
    #     return Response(status=status.HTTP_200_OK, data=data)

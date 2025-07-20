from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from JobRecServer.apps.job.models import Job
from JobRecServer.apps.middle.models import ClickJob, CompanyCode
from JobRecServer.apps.student.models import Student
from JobRecServer.apps.user.models import User
from datetime import datetime, timedelta
import pandas as pd
from openpyxl import Workbook
import os
import random
from django.utils import timezone

# 核心职业推荐API
@api_view(['GET'])
def job_recommendations(request):
    """
    获取职业推荐列表
    参数:
    - user_id: 学生ID (可选)
    - page: 页码 (可选)
    - size: 每页数量 (可选)
    """
    try:
        # 这里应该调用您的推荐算法
        # 示例: 随机返回10个有效职位
        valid_jobs = Job.objects.filter(
            create_time__gte=timezone.now()-timedelta(days=30)
        ).order_by('?')[:10]
        
        results = [{
            'job_id': job.DWZZJGDM,
            'company': job.SJDWMC,
            'position': job.GZZWLBMC,
            'salary': job.salary,
            'location': job.DWSZDDM,
            'major_required': job.major,
            'description': job.desc[:100] + '...' if job.desc else ''
        } for job in valid_jobs]
        
        return Response({
            'status': 'success',
            'data': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


# 技能分析API
@api_view(['GET'])
def skill_analysis(request, user_id):
    """
    获取学生技能分析
    参数:
    - user_id: 学生ID (必需)
    """
    try:
        student = Student.objects.get(SID=user_id)
        
        # 这里应该是您的技能分析逻辑
        # 示例: 基于专业和点击历史的简单分析
        clicked_jobs = ClickJob.objects.filter(
            student=student
        ).values_list('job__major', flat=True)
        
        major_distribution = pd.Series(clicked_jobs).value_counts().to_dict()
        
        return Response({
            'status': 'success',
            'data': {
                'student_id': student.SID,
                'name': student.REALNAME,
                'major': student.MAJOR,
                'interest_areas': major_distribution,
                'suggested_skills': ["Python", "机器学习", "数据分析"]  # 示例数据
            }
        })
    
    except Student.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Student not found'
        }, status=404)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


# 职业路径规划API
@api_view(['GET'])
def career_path(request, user_id):
    """
    获取职业发展路径建议
    参数:
    - user_id: 学生ID (必需)
    """
    try:
        student = Student.objects.get(SID=user_id)
        
        # 这里应该是您的职业路径算法
        # 示例: 基于专业的简单路径建议
        career_paths = {
            "计算机技术": [
                {"stage": "初级", "position": "软件开发工程师", "skills": ["Python", "Java"]},
                {"stage": "中级", "position": "高级开发工程师", "skills": ["系统设计", "架构"]},
                {"stage": "高级", "position": "技术总监", "skills": ["团队管理", "项目管理"]}
            ],
            "电子信息": [
                {"stage": "初级", "position": "硬件工程师", "skills": ["电路设计", "PCB"]},
                {"stage": "中级", "position": "系统工程师", "skills": ["嵌入式系统", "FPGA"]},
                {"stage": "高级", "position": "首席工程师", "skills": ["技术规划", "创新管理"]}
            ]
        }
        
        path = career_paths.get(student.MAJOR, career_paths["计算机技术"])
        
        return Response({
            'status': 'success',
            'data': {
                'student_id': student.SID,
                'name': student.REALNAME,
                'major': student.MAJOR,
                'career_path': path
            }
        })
    
    except Student.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Student not found'
        }, status=404)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


# 数据导出API (供管理员使用)
@api_view(['GET'])
def export_student_data(request):
    """
    导出学生数据为Excel
    需要管理员权限
    """
    try:
        if not request.user.is_staff:
            return Response({
                'status': 'error',
                'message': 'Permission denied'
            }, status=403)
        
        base_dir = "data/xdu/"
        os.makedirs(base_dir, exist_ok=True)
        file_name = "xdu_dataset_user.xlsx"
        file_path = os.path.join(base_dir, file_name)
        
        students = Student.objects.all()
        
        workbook = Workbook()
        worksheet = workbook.active
        
        # 写入表头
        worksheet.append([
            "SID", "REALNAME", "MAJOR", "DEPARTMENT", 
            "XLMC", "BIRTHDAY", "XBMC"
        ])
        
        # 写入数据
        for student in students:
            worksheet.append([
                student.SID or "",
                student.REALNAME or "",
                student.MAJOR or "",
                student.DEPARTMENT or "",
                student.XLMC or "",
                student.BIRTHDAY or "",
                student.XBMC or ""
            ])
        
        workbook.save(file_path)
        
        return Response({
            'status': 'success',
            'message': f'Data exported to {file_path}',
            'file_path': file_path
        })
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)


# API路由配置
urlpatterns = [
    path('recommendations/', job_recommendations, name='job-recommendations'),
    path('skill-analysis/<str:user_id>/', skill_analysis, name='skill-analysis'),
    path('career-path/<str:user_id>/', career_path, name='career-path'),
    path('export/students/', export_student_data, name='export-students'),
]
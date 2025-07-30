# knowledgeGraph/api_urls.py
"""
知识图谱API接口的URL配置
"""
from django.urls import path
from . import api_views

app_name = 'Graphapps_api'

urlpatterns = [
    # 查询接口
    path('query/', api_views.query_api, name='query'),
    
    # 图谱数据接口
    path('graph_data/', api_views.get_graph_data_api, name='graph_data'),
    
    # 更新检查接口
    path('check_updates/', api_views.check_updates_api, name='check_updates'),
    
    # 统计信息接口
    path('statistics/', api_views.statistics_api, name='statistics'),
    
    # 采集任务接口
    path('run_collection/', api_views.run_collection_api, name='run_collection'),
    
    # 进度查询接口
    path('collection_progress/', api_views.get_collection_progress_api, name='collection_progress'),
    
    # 实体搜索接口
    path('search_entities/', api_views.search_entities_api, name='search_entities'),
    
    # 路径查找接口
    path('find_path/', api_views.find_path_api, name='find_path'),
    
    # 相关实体查找接口
    path('find_related/', api_views.find_related_api, name='find_related'),
    
    # 知识点列表接口
    path('knowledge_points/', api_views.get_knowledge_points_api, name='knowledge_points'),
    
    # 课程列表接口
    path('courses/', api_views.get_courses_api, name='courses'),
]

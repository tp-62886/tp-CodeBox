# Graphapps/urls.py
"""
知识图谱应用的URL配置
"""
from django.urls import path, include
from . import views

app_name = 'Graphapps'

urlpatterns = [
    # 主页
    path('', views.index, name='index'),

    # 管理面板
    path('admin/', views.admin_panel, name='admin_panel'),

    # 查询接口
    path('query/', views.query, name='query'),

    # 图谱数据接口
    path('get_graph_data/', views.get_graph_data, name='get_graph_data'),

    # 统计信息接口
    path('statistics/', views.get_statistics_api, name='statistics'),

    # 采集任务接口
    path('run_collection/', views.run_collection_api, name='run_collection'),

    # 进度查询接口
    path('get_collection_progress/', views.get_collection_progress_api, name='get_collection_progress'),

    # 更新检查接口
    path('check_updates/', views.check_updates, name='check_updates'),

    # Neo4j状态检查接口
    path('check_neo4j_status/', views.check_neo4j_status_api, name='check_neo4j_status'),

    # 从Neo4j重新加载数据接口
    path('reload_from_neo4j/', views.reload_data_from_neo4j_api, name='reload_from_neo4j'),

    # API接口
    path('api/', include('Graphapps.api_urls')),

    # 测试页面
    path('test/', views.test_page, name='test_page'),
    path('debug/', views.debug_data, name='debug_data'),
    path('test_data_source/', views.test_data_source, name='test_data_source'),
]

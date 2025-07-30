# knowledgeGraph/api_views.py
"""
知识图谱API视图函数
"""
import json
import time
import subprocess
import sys
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

try:
    from .knowledgeGraph_api import knowledge_graph_api
except ImportError:
    # 如果无法导入，创建一个简单的替代实现
    class SimpleKnowledgeGraphAPI:
        def search_entities(self, search_term):
            return {'success': False, 'error': '知识图谱API未正确初始化'}

        def get_graph_data(self, max_nodes=500):
            return {'success': False, 'error': '知识图谱API未正确初始化'}

        def get_statistics(self):
            return {'success': False, 'error': '知识图谱API未正确初始化'}

        def get_knowledge_points(self):
            return {'success': False, 'error': '知识图谱API未正确初始化'}

        def get_courses(self):
            return {'success': False, 'error': '知识图谱API未正确初始化'}

        def find_path(self, source, target):
            return {'success': False, 'error': '知识图谱API未正确初始化'}

        def find_related(self, entity_name):
            return {'success': False, 'error': '知识图谱API未正确初始化'}

    knowledge_graph_api = SimpleKnowledgeGraphAPI()

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def query_api(request):
    """查询接口API"""
    try:
        data = json.loads(request.body)
        query_text = data.get('query', '')
        
        # 解析查询内容
        if 'search' in query_text.lower():
            # 搜索实体
            search_term = query_text.lower().replace('search', '').strip()
            result = knowledge_graph_api.search_entities(search_term)
        elif 'path' in query_text.lower():
            # 查找路径
            parts = query_text.split()
            if len(parts) >= 3:
                source = parts[-2]
                target = parts[-1]
                result = knowledge_graph_api.find_path(source, target)
            else:
                result = {'success': False, 'error': '路径查询格式错误，请使用: path 源实体 目标实体'}
        elif 'related' in query_text.lower():
            # 查找相关实体
            entity_name = query_text.lower().replace('related', '').strip()
            result = knowledge_graph_api.find_related(entity_name)
        elif ('知识点' in query_text.lower() or 
              'knowledge' in query_text.lower() or 
              'point' in query_text.lower()):
            # 返回所有知识点
            result = knowledge_graph_api.get_knowledge_points()
        elif ('课程' in query_text.lower() or 
              'course' in query_text.lower()):
            # 返回所有课程
            result = knowledge_graph_api.get_courses()
        elif '整个' in query_text.lower() or '全部' in query_text.lower():
            # 返回整个图谱
            result = knowledge_graph_api.get_graph_data()
        else:
            # 默认返回整个图谱
            result = knowledge_graph_api.get_graph_data()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"查询API错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_graph_data_api(request):
    """获取图谱数据API"""
    try:
        max_nodes = int(request.GET.get('max_nodes', 500))
        result = knowledge_graph_api.get_graph_data(max_nodes)
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"获取图谱数据API错误: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def check_updates_api(request):
    """检查更新API"""
    try:
        data = json.loads(request.body)
        last_update = data.get('last_update', 0)
        
        # 检查文件修改时间
        latest_update = last_update
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        json_path = os.path.join(base_dir, 'apps', 'knowledge_graph.json')
        if os.path.exists(json_path):
            file_time = os.path.getmtime(json_path)
            if file_time > latest_update:
                latest_update = file_time
                
        pickle_path = os.path.join(base_dir, 'apps', 'knowledge_graph.pkl')
        if os.path.exists(pickle_path):
            file_time = os.path.getmtime(pickle_path)
            if file_time > latest_update:
                latest_update = file_time
                
        collected_path = os.path.join(base_dir, 'apps', 'data', 'collected_knowledge.json')
        if os.path.exists(collected_path):
            file_time = os.path.getmtime(collected_path)
            if file_time > latest_update:
                latest_update = file_time
        
        return JsonResponse({
            'success': True,
            'has_updates': latest_update > last_update,
            'latest_update': latest_update
        })
    except Exception as e:
        logger.error(f"检查更新API错误: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def statistics_api(request):
    """统计信息API"""
    try:
        result = knowledge_graph_api.get_statistics()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"统计信息API错误: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def run_collection_api(request):
    """运行采集任务API"""
    try:
        data = json.loads(request.body)
        collection_type = data.get('collection_type', 'continue')
        
        # 构建命令
        if collection_type == 'reset':
            cmd = [sys.executable, '-m', 'Graphapps.run', '--reset']
        elif collection_type == 'continue':
            cmd = [sys.executable, '-m', 'Graphapps.run', '--continue-collection']
        else:
            cmd = [sys.executable, '-m', 'Graphapps.run']  # 默认执行
        
        # 创建进度文件目录（如果不存在）
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(base_dir, 'apps', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # 记录开始采集的信息到进度文件
        progress_file = os.path.join(data_dir, 'collection_progress.json')
        progress_info = {
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'running',
            'collection_type': collection_type
        }
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_info, f, ensure_ascii=False, indent=2)
        
        # 启动后台进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=base_dir
        )
        
        return JsonResponse({
            'success': True,
            'message': f'采集任务已启动 (PID: {process.pid})',
            'collection_type': collection_type
        })
        
    except Exception as e:
        logger.error(f"运行采集任务API错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_collection_progress_api(request):
    """获取采集进度API"""
    try:
        # 读取进度文件
        progress_info = {
            'last_batch': 0,
            'total_batches': 0,
            'last_updated': '未知',
            'processed_topics': [],
            'status': 'idle'
        }
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        progress_file = os.path.join(base_dir, 'apps', 'data', 'collection_progress.json')
        
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                progress_info.update(progress_data)
        
        return JsonResponse({
            'success': True,
            'progress': progress_info
        })
    except Exception as e:
        logger.error(f"获取采集进度API错误: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def search_entities_api(request):
    """搜索实体API"""
    try:
        data = json.loads(request.body)
        search_term = data.get('search_term', '')
        
        if not search_term:
            return JsonResponse({
                'success': False,
                'error': '搜索词不能为空'
            }, status=400)
        
        result = knowledge_graph_api.search_entities(search_term)
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"搜索实体API错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def find_path_api(request):
    """查找路径API"""
    try:
        data = json.loads(request.body)
        source = data.get('source', '')
        target = data.get('target', '')
        
        if not source or not target:
            return JsonResponse({
                'success': False,
                'error': '源实体和目标实体不能为空'
            }, status=400)
        
        result = knowledge_graph_api.find_path(source, target)
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"查找路径API错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def find_related_api(request):
    """查找相关实体API"""
    try:
        data = json.loads(request.body)
        entity_name = data.get('entity_name', '')
        
        if not entity_name:
            return JsonResponse({
                'success': False,
                'error': '实体名称不能为空'
            }, status=400)
        
        result = knowledge_graph_api.find_related(entity_name)
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"查找相关实体API错误: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_knowledge_points_api(request):
    """获取知识点API"""
    try:
        result = knowledge_graph_api.get_knowledge_points()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"获取知识点API错误: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def get_courses_api(request):
    """获取课程API"""
    try:
        result = knowledge_graph_api.get_courses()
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"获取课程API错误: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

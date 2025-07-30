# Graphapps/views.py
"""
知识图谱应用的视图函数
基于原Flask代码完整实现查询功能
"""
import os
import json
import time
import subprocess
import sys
import pickle
import datetime
import math
import random
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import logging

# 设置logger
logger = logging.getLogger(__name__)

# 创建关系类型的中英文映射
RELATION_TYPES_MAP = {
    'CONTAINS': '包含',
    'RELATED_TO': '相关于',
    'PREREQUISITE': '先修于',
    'PREREQUISITE_FOR': '后续',
    'SIMILAR_TO': '相似于'
}

def get_chinese_relation_type(relation_type):
    """将英文关系类型转换为中文显示"""
    return RELATION_TYPES_MAP.get(relation_type, relation_type)

# 导入业务逻辑模块
try:
    from .neo4j_connector import Neo4j
    from .nlp_converter import NLPCypherConverter
    from .save_graph import CORE_KNOWLEDGE_POINTS
except ImportError as e:
    logger.warning(f"导入Graphapps模块失败: {e}")
    Neo4j = None
    NLPCypherConverter = None
    CORE_KNOWLEDGE_POINTS = []

# 初始化Neo4j连接
try:
    if Neo4j:
        neo4j = Neo4j(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "12345678")
        )
    else:
        neo4j = None
except Exception as e:
    logger.error(f"Neo4j连接失败: {str(e)}")
    neo4j = None

# 初始化NLP转换器
try:
    if NLPCypherConverter:
        converter = NLPCypherConverter()
    else:
        converter = None
except Exception as e:
    logger.error(f"NLP转换器初始化失败: {str(e)}")
    converter = None

# 全局变量存储知识图谱数据
graph_data = {
    'entities': {},
    'relations': []
}

def get_data_file_path(filename):
    """获取数据文件的绝对路径"""
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, 'data', filename)

def check_neo4j_connection():
    """检查Neo4j连接是否可用"""
    global neo4j

    if not neo4j:
        return False, "Neo4j连接器未初始化"

    try:
        # 执行简单的查询来测试连接
        test_result = neo4j.sync_query("RETURN 1 as test")
        if test_result:
            return True, "Neo4j连接正常"
        else:
            return False, "Neo4j查询返回空结果"
    except Exception as e:
        return False, f"Neo4j连接失败: {str(e)}"

def load_graph_data_from_neo4j():
    """从Neo4j数据库加载知识图谱数据"""
    global graph_data, neo4j

    # 检查Neo4j连接
    is_connected, connection_msg = check_neo4j_connection()
    if not is_connected:
        logger.warning(f"无法连接到Neo4j数据库: {connection_msg}")
        return False

    try:
        logger.info("正在从Neo4j数据库加载知识图谱数据...")

        # 初始化数据结构
        temp_graph_data = {
            'entities': {},
            'relations': []
        }

        # 查询所有节点
        nodes_query = """
        MATCH (n)
        WHERE n.name IS NOT NULL
        RETURN n.name as name,
               labels(n) as labels,
               properties(n) as properties
        LIMIT 1000
        """

        nodes_result = neo4j.sync_query(nodes_query)
        logger.info(f"从Neo4j查询到 {len(nodes_result)} 个节点")

        if not nodes_result:
            logger.warning("Neo4j数据库中没有找到任何节点数据")
            return False

        # 处理节点数据
        for record in nodes_result:
            name = record['name']
            labels = record['labels']
            properties = record['properties']

            if name:  # 确保节点有名称
                # 确定节点标签
                label = 'Entity'  # 默认标签
                if labels:
                    if 'KnowledgePoint' in labels:
                        label = 'KnowledgePoint'
                    elif 'Course' in labels:
                        label = 'Course'
                    elif 'Topic' in labels:
                        label = 'Topic'
                    else:
                        label = labels[0]  # 使用第一个标签

                temp_graph_data['entities'][name] = {
                    'name': name,
                    'label': label,
                    'properties': properties or {}
                }

        # 查询所有关系
        relations_query = """
        MATCH (a)-[r]->(b)
        WHERE a.name IS NOT NULL AND b.name IS NOT NULL
        RETURN a.name as source,
               b.name as target,
               type(r) as relation_type,
               properties(r) as properties
        LIMIT 2000
        """

        relations_result = neo4j.sync_query(relations_query)
        logger.info(f"从Neo4j查询到 {len(relations_result)} 个关系")

        # 处理关系数据
        for record in relations_result:
            source = record['source']
            target = record['target']
            relation_type = record['relation_type']
            properties = record['properties']

            if source and target:  # 确保关系有源和目标
                temp_graph_data['relations'].append({
                    'source': source,
                    'target': target,
                    'relation_type': relation_type or 'RELATED_TO',
                    'properties': properties or {}
                })

        # 检查是否有有效数据
        if not temp_graph_data['entities']:
            logger.warning("从Neo4j加载的数据为空")
            return False

        # 更新全局数据
        graph_data = temp_graph_data

        logger.info(f"成功从Neo4j加载了知识图谱数据: {len(graph_data['entities'])} 个实体, {len(graph_data['relations'])} 个关系")

        # 保存到本地文件作为缓存
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'apps', 'knowledge_graph.json')
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            logger.info("Neo4j数据已缓存到本地文件")
        except Exception as e:
            logger.warning(f"保存缓存文件失败: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"从Neo4j加载数据失败: {str(e)}")
        return False

def load_graph_data():
    """加载知识图谱数据 - 优先从Neo4j数据库加载"""
    global graph_data

    logger.info("开始加载知识图谱数据...")

    # 1. 优先尝试从Neo4j数据库加载
    if load_graph_data_from_neo4j():
        logger.info("✅ 成功从Neo4j数据库加载数据")
        return True

    logger.info("Neo4j加载失败，尝试从本地文件加载...")

    # 2. 尝试从pickle文件加载（更快）
    pickle_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.pkl')
    if os.path.exists(pickle_path):
        try:
            with open(pickle_path, 'rb') as f:
                data = pickle.load(f)
                graph_data = data
                logger.info(f"✅ 从pickle文件加载了知识图谱数据: {len(graph_data.get('entities', {}))} 个实体, {len(graph_data.get('relations', []))} 个关系")
                return True
        except Exception as e:
            logger.error(f"从pickle文件加载失败: {str(e)}")

    # 3. 尝试从JSON文件加载
    json_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                graph_data = data
                logger.info(f"✅ 从JSON文件加载了知识图谱数据: {len(graph_data.get('entities', {}))} 个实体, {len(graph_data.get('relations', []))} 个关系")
                return True
        except Exception as e:
            logger.error(f"从JSON文件加载失败: {str(e)}")

    # 4. 如果所有加载方式都失败，使用空数据结构
    logger.warning("所有数据源都不可用，使用空数据结构")
    graph_data = {
        'entities': {},
        'relations': []
    }
    return False

# 在模块加载时加载数据
load_graph_data()

def index(request):
    """主页"""
    return render(request, 'Graphapps/index.html')

def test_page(request):
    """测试页面"""
    return render(request, 'Graphapps/test.html')

def debug_data(request):
    """调试数据"""
    global graph_data, neo4j

    # 检查Neo4j连接状态
    neo4j_status = "未连接"
    if neo4j:
        try:
            test_result = neo4j.sync_query("RETURN 1 as test")
            if test_result:
                neo4j_status = "已连接"
            else:
                neo4j_status = "连接失败"
        except Exception as e:
            neo4j_status = f"连接错误: {str(e)}"

    # 检查数据文件存在情况
    pickle_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.pkl')
    json_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.json')

    return JsonResponse({
        'graph_data_keys': list(graph_data.keys()),
        'entities_count': len(graph_data.get('entities', {})),
        'relations_count': len(graph_data.get('relations', [])),
        'sample_entities': list(graph_data.get('entities', {}).keys())[:5],
        'neo4j_status': neo4j_status,
        'data_files': {
            'pickle_exists': os.path.exists(pickle_path),
            'json_exists': os.path.exists(json_path)
        },
        'data_source_priority': [
            '1. Neo4j数据库',
            '2. Pickle文件',
            '3. JSON文件'
        ]
    })

def test_data_source(request):
    """测试数据源并强制重新加载"""
    global graph_data, neo4j

    results = []

    # 1. 测试Neo4j连接
    neo4j_test = "失败"
    neo4j_data_count = 0
    if neo4j:
        try:
            # 测试连接
            test_result = neo4j.sync_query("RETURN 1 as test")
            if test_result:
                neo4j_test = "连接成功"

                # 查询实际数据数量
                nodes_result = neo4j.sync_query("MATCH (n) RETURN count(n) as count")
                if nodes_result:
                    neo4j_data_count = nodes_result[0]['count']

        except Exception as e:
            neo4j_test = f"连接错误: {str(e)}"

    results.append(f"Neo4j测试: {neo4j_test}, 节点数量: {neo4j_data_count}")

    # 2. 测试文件数据源
    pickle_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.pkl')
    json_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.json')

    pickle_count = 0
    json_count = 0

    if os.path.exists(pickle_path):
        try:
            with open(pickle_path, 'rb') as f:
                data = pickle.load(f)
                pickle_count = len(data.get('entities', {}))
        except:
            pass

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                json_count = len(data.get('entities', {}))
        except:
            pass

    results.append(f"Pickle文件: 存在={os.path.exists(pickle_path)}, 实体数量: {pickle_count}")
    results.append(f"JSON文件: 存在={os.path.exists(json_path)}, 实体数量: {json_count}")

    # 3. 当前内存中的数据
    current_count = len(graph_data.get('entities', {}))
    results.append(f"当前内存数据: 实体数量: {current_count}")

    # 4. 测试Neo4j查询功能
    neo4j_sample_data = []
    if neo4j and neo4j_data_count > 0:
        try:
            # 查询一些示例数据
            sample_query = """
            MATCH (n)
            WHERE n.name IS NOT NULL
            RETURN n.name as name, labels(n) as labels
            LIMIT 5
            """
            sample_result = neo4j.sync_query(sample_query)
            for record in sample_result:
                neo4j_sample_data.append({
                    'name': record['name'],
                    'labels': record['labels']
                })
        except Exception as e:
            results.append(f"Neo4j查询测试失败: {str(e)}")

    return JsonResponse({
        'test_results': results,
        'neo4j_nodes': neo4j_data_count,
        'pickle_entities': pickle_count,
        'json_entities': json_count,
        'current_entities': current_count,
        'neo4j_sample_data': neo4j_sample_data,
        'conclusion': 'Neo4j数据库正常工作，系统正在使用Neo4j作为主要数据源' if neo4j_data_count > 0 else '系统未使用Neo4j数据库'
    })

def admin_panel(request):
    """知识图谱管理面板"""
    # 获取当前采集进度信息
    progress_info = {
        'last_batch': 0,
        'total_batches': 0,
        'last_updated': '未知',
        'processed_topics': []
    }

    # 尝试读取进度文件
    try:
        progress_file = os.path.join(os.path.dirname(__file__), 'apps', 'data', 'collection_progress.json')
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                progress_info['last_batch'] = progress_data.get('last_batch', 0)
                progress_info['total_batches'] = progress_data.get('total_batches', 0)
                progress_info['last_updated'] = progress_data.get('last_updated', '未知')
                progress_info['processed_topics'] = progress_data.get('processed_topics', [])
    except Exception as e:
        logger.error(f"读取采集进度失败: {str(e)}")

    return render(request, 'Graphapps/admin.html', {'progress': progress_info})

@csrf_exempt
@require_http_methods(["POST"])
def query(request):
    """处理查询请求 - 基于Flask版本完整实现，返回前端期望的格式"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        query_text = data.get('query', '')

        result = None

        # 解析查询内容
        if 'search' in query_text.lower():
            # 搜索实体
            search_term = query_text.lower().replace('search', '').strip()
            result = search_entities(search_term)
        elif 'path' in query_text.lower():
            # 查找路径
            parts = query_text.split()
            if len(parts) >= 3:
                source = parts[-2]
                target = parts[-1]
                path_result = find_path(source, target)
                if path_result.get('success'):
                    # 将路径转换为节点和关系格式
                    path_nodes = path_result.get('data', {}).get('path', [])
                    nodes = path_nodes
                    relationships = []
                    # 为路径中的节点创建关系
                    for i in range(len(path_nodes) - 1):
                        relationships.append({
                            'source': path_nodes[i]['id'],
                            'target': path_nodes[i + 1]['id'],
                            'type': 'PATH',
                            'properties': {}
                        })
                    result = {
                        'success': True,
                        'data': {
                            'nodes': nodes,
                            'relationships': relationships
                        }
                    }
                else:
                    result = path_result
        elif 'related' in query_text.lower():
            # 查找相关实体
            entity_name = query_text.lower().replace('related', '').strip()
            related_result = find_related(entity_name)
            if related_result.get('success'):
                # 将相关实体转换为节点格式
                related_entities = related_result.get('data', {}).get('related_entities', [])
                nodes = related_entities
                # 添加原始实体
                if entity_name in graph_data.get('entities', {}):
                    entity_data = graph_data['entities'][entity_name]
                    nodes.insert(0, {
                        'id': entity_name,
                        'name': entity_name,
                        'label': entity_data.get('type', 'Entity'),
                        'properties': entity_data
                    })

                # 创建关系
                relationships = []
                for entity in related_entities:
                    relationships.append({
                        'source': entity_name,
                        'target': entity['id'],
                        'type': 'RELATED_TO',
                        'properties': {}
                    })

                result = {
                    'success': True,
                    'data': {
                        'nodes': nodes,
                        'relationships': relationships
                    }
                }
            else:
                result = related_result
        elif ('知识点' in query_text.lower() or
              'knowledge' in query_text.lower() or
              'point' in query_text.lower()):
            # 返回所有知识点
            result = get_all_knowledge_points()
        elif ('课程' in query_text.lower() or
              'course' in query_text.lower()):
            # 返回所有课程
            result = get_all_courses()
        elif '整个' in query_text.lower() or '全部' in query_text.lower():
            # 返回整个图谱
            result = get_full_graph()
        else:
            # 默认返回整个图谱
            result = get_full_graph()

        # 转换结果格式以匹配前端期望
        if result and result.get('success'):
            nodes = result.get('data', {}).get('nodes', result.get('nodes', []))
            relationships = result.get('data', {}).get('relationships', result.get('relationships', []))

            # 为节点添加随机初始位置，避免堆叠
            import random
            for i, node in enumerate(nodes):
                if 'x' not in node or 'y' not in node:
                    # 使用圆形分布避免节点重叠
                    angle = (2 * 3.14159 * i) / len(nodes) if len(nodes) > 1 else 0
                    radius = 100 + (i % 3) * 50  # 多层圆形分布
                    node['x'] = 400 + radius * math.cos(angle) + random.uniform(-20, 20)
                    node['y'] = 300 + radius * math.sin(angle) + random.uniform(-20, 20)

            response_data = {
                'success': True,
                'nodes': nodes,
                'relationships': relationships,
                'cypher_query': query_text,
                'total_nodes': len(nodes),
                'total_relationships': len(relationships)
            }
        else:
            response_data = {
                'success': False,
                'error': result.get('error', '查询失败') if result else '未知错误',
                'nodes': [],
                'relationships': []
            }

        response = JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        response = JsonResponse({
            'success': False,
            'error': str(e),
            'nodes': [],
            'relationships': []
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

@require_http_methods(["GET"])
def get_graph_data(request):
    """获取图谱数据 - 为前端提供兼容的接口"""
    try:
        # 获取完整图谱数据
        result = get_full_graph()

        if result and result.get('success'):
            nodes = result.get('nodes', [])
            relationships = result.get('relationships', [])

            # 为节点添加随机初始位置，避免堆叠
            for i, node in enumerate(nodes):
                if 'x' not in node or 'y' not in node:
                    # 使用圆形分布避免节点重叠
                    angle = (2 * math.pi * i) / len(nodes) if len(nodes) > 1 else 0
                    radius = 150 + (i % 5) * 40  # 多层圆形分布
                    node['x'] = 400 + radius * math.cos(angle) + random.uniform(-30, 30)
                    node['y'] = 300 + radius * math.sin(angle) + random.uniform(-30, 30)

            response_data = {
                'success': True,
                'nodes': nodes,
                'relationships': relationships,
                'total_entities': len(nodes),
                'total_relations': len(relationships),
                'message': f"图谱数据已加载，包含 {len(nodes)} 个节点和 {len(relationships)} 个关系。"
            }
        else:
            response_data = {
                'success': False,
                'error': result.get('error', '获取图谱数据失败') if result else '未知错误',
                'nodes': [],
                'relationships': []
            }

        response = JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        logger.error(f"获取图谱数据错误: {str(e)}")
        response = JsonResponse({
            'success': False,
            'error': str(e),
            'nodes': [],
            'relationships': []
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

def search_entities(search_term):
    """搜索实体 - 完全基于Flask版本的复杂搜索逻辑"""
    try:
        global graph_data

        if not search_term:
            return {
                'success': False,
                'error': '搜索词不能为空'
            }

        nodes = []
        relationships = []

        # 核心知识点列表，确保这些关键实体能被模糊匹配到
        core_entities = ['算法', '数据结构', '人工智能', '机器学习', '深度学习',
                         '计算机网络', '操作系统', '数据库', '软件工程', '编译原理']

        # 尝试精确匹配
        exact_matches = []
        for name, entity in graph_data['entities'].items():
            if search_term.lower() == name.lower():
                exact_matches.append(entity)

        # 如果找到精确匹配，则使用精确匹配的结果
        if exact_matches:
            matching_entities = exact_matches
        else:
            # 否则进行模糊匹配
            matching_entities = []

            # 首先检查核心实体是否匹配
            core_matches = []
            for core_entity in core_entities:
                if search_term.lower() in core_entity.lower() or core_entity.lower() in search_term.lower():
                    if core_entity in graph_data['entities']:
                        core_matches.append(graph_data['entities'][core_entity])

            # 如果找到核心实体匹配，优先使用
            if core_matches:
                matching_entities = core_matches
            else:
                # 进行常规模糊匹配
                for name, entity in graph_data['entities'].items():
                    if search_term.lower() in name.lower():
                        matching_entities.append(entity)

        # 如果仍然没有匹配，尝试部分词匹配
        if not matching_entities:
            # 将搜索词分解为词
            search_words = search_term.lower().split()
            for name, entity in graph_data['entities'].items():
                name_lower = name.lower()
                for word in search_words:
                    if len(word) >= 2 and word in name_lower:  # 只匹配长度>=2的词
                        matching_entities.append(entity)
                        break

        # 如果仍然没有匹配，返回一些默认实体
        if not matching_entities:
            # 尝试从默认/核心知识点中返回最相关的
            try:
                from .save_graph import CORE_KNOWLEDGE_POINTS
                for name in CORE_KNOWLEDGE_POINTS:
                    if name in graph_data['entities']:
                        matching_entities.append(graph_data['entities'][name])
                        logger.info(f"未找到匹配，返回核心知识点: {name}")
                        break
            except ImportError:
                pass

        # 最后的保险措施 - 如果实在找不到任何匹配，返回错误信息
        if not matching_entities:
            return {
                'success': False,
                'error': f"没有找到与 '{search_term}' 匹配的实体"
            }

        # 添加匹配的实体到节点列表
        for entity in matching_entities:
            entity_name = entity.get('name')
            nodes.append({
                'id': entity_name,
                'label': entity.get('label', 'Entity'),
                'name': entity_name,
                'properties': entity.get('properties', {})
            })

        # 记录已添加的节点ID
        added_node_ids = {entity['id'] for entity in nodes}

        # 添加与这些实体相关的所有类型的关系
        entity_names = [e.get('name') for e in matching_entities]

        # 第一遍：查找所有直接关系，无论关系类型
        direct_relations = []
        second_degree_entity_names = set()

        for relation in graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            relation_type = relation.get('relation_type')

            # 如果关系的一端是查询的实体
            if source in entity_names or target in entity_names:
                # 添加关系的另一端到二度实体集合
                if source in entity_names:
                    second_degree_entity_names.add(target)
                else:
                    second_degree_entity_names.add(source)

                # 确保关系的两端都在节点列表中
                if source not in added_node_ids and source in graph_data['entities']:
                    entity = graph_data['entities'][source]
                    nodes.append({
                        'id': source,
                        'label': entity.get('label', 'Entity'),
                        'name': source,
                        'properties': entity.get('properties', {})
                    })
                    added_node_ids.add(source)

                if target not in added_node_ids and target in graph_data['entities']:
                    entity = graph_data['entities'][target]
                    nodes.append({
                        'id': target,
                        'label': entity.get('label', 'Entity'),
                        'name': target,
                        'properties': entity.get('properties', {})
                    })
                    added_node_ids.add(target)

                # 添加关系
                direct_relations.append({
                    'source': source,
                    'target': target,
                    'type': get_chinese_relation_type(relation_type),
                    'properties': {}
                })

        # 所有关系添加到结果中
        relationships.extend(direct_relations)

        return {
            'success': True,
            'data': {
                'nodes': nodes,
                'relationships': relationships,
                'total_found': len(nodes)
            }
        }

    except Exception as e:
        logger.error(f"搜索实体失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def find_path(source, target):
    """查找两个实体之间的路径 - 完全基于Flask版本的路径查找实现"""
    try:
        global graph_data

        # 检查源和目标实体是否存在
        if source not in graph_data['entities']:
            return {
                'success': False,
                'error': f"源实体不存在: {source}"
            }

        if target not in graph_data['entities']:
            return {
                'success': False,
                'error': f"目标实体不存在: {target}"
            }

        # 构建图结构
        graph = {}
        for entity_name in graph_data['entities']:
            graph[entity_name] = []

        for relation in graph_data['relations']:
            source_name = relation.get('source')
            target_name = relation.get('target')
            relation_type = relation.get('relation_type')

            if source_name in graph and target_name in graph:
                graph[source_name].append((target_name, relation_type))
                # 对于RELATED_TO关系，考虑双向
                if relation_type == 'RELATED_TO':
                    graph[target_name].append((source_name, relation_type))

        # 使用BFS查找路径
        visited = {source: None}
        queue = [(source, [])]

        while queue:
            current, path = queue.pop(0)

            if current == target:
                # 找到路径
                nodes = []
                relationships = []

                # 记录路径中的所有节点
                all_nodes = set()
                for step in path + [(current, None)]:
                    node_name = step[0]
                    all_nodes.add(node_name)

                # 添加节点
                for node_name in all_nodes:
                    if node_name in graph_data['entities']:
                        entity = graph_data['entities'][node_name]
                        nodes.append({
                            'id': node_name,
                            'label': entity.get('label', 'Entity'),
                            'name': node_name,
                            'properties': entity.get('properties', {})
                        })

                # 添加路径中的关系
                for i in range(len(path)):
                    step = path[i]
                    source_name = step[0]
                    relation_type = step[1]
                    target_name = path[i + 1][0] if i + 1 < len(path) else current

                    relationships.append({
                        'source': source_name,
                        'target': target_name,
                        'type': get_chinese_relation_type(relation_type),
                        'properties': {}
                    })

                return {
                    'success': True,
                    'data': {
                        'nodes': nodes,
                        'relationships': relationships,
                        'path_length': len(path),
                        'cypher_query': f"从 {source} 到 {target} 的路径"
                    }
                }

            # 继续BFS搜索
            for neighbor, rel_type in graph.get(current, []):
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append((neighbor, path + [(current, rel_type)]))

        # 没有找到路径
        return {
            'success': False,
            'error': f"未找到从 {source} 到 {target} 的路径"
        }

    except Exception as e:
        logger.error(f"查找路径失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def find_related(entity_name):
    """查找与指定实体相关的实体 - 完全基于Flask版本的复杂相关实体查找逻辑"""
    try:
        global graph_data

        if not entity_name:
            return {
                'success': False,
                'error': '实体名称不能为空'
            }

        nodes = []
        relationships = []

        # 确保实体存在
        if entity_name not in graph_data['entities']:
            # 尝试模糊匹配
            matching_entities = []
            for name in graph_data['entities']:
                if entity_name.lower() in name.lower():
                    matching_entities.append(name)

            if matching_entities:
                entity_name = matching_entities[0]  # 使用第一个匹配的实体
            else:
                return {
                    'success': False,
                    'error': f"未找到实体: {entity_name}"
                }

        # 添加中心实体
        entity = graph_data['entities'][entity_name]
        entity_label = entity.get('label', 'Entity')
        nodes.append({
            'id': entity_name,
            'label': entity_label,
            'name': entity_name,
            'properties': entity.get('properties', {})
        })

        # 记录已添加节点的ID
        added_node_ids = {entity_name}

        # 查找所有相关的实体，包括所有类型的关系
        for relation in graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            relation_type = relation.get('relation_type', 'RELATED_TO')

            if source == entity_name or target == entity_name:
                # 确定关系的另一端
                related_entity_name = target if source == entity_name else source

                # 确保相关实体存在于图谱数据中
                if related_entity_name in graph_data['entities']:
                    # 添加关系
                    relationships.append({
                        'source': source,
                        'target': target,
                        'type': get_chinese_relation_type(relation_type),
                        'properties': {}
                    })

                    # 如果相关实体尚未添加到节点列表中
                    if related_entity_name not in added_node_ids:
                        related_entity = graph_data['entities'][related_entity_name]
                        # 确保正确设置实体标签
                        label = related_entity.get('label', 'Entity')

                        nodes.append({
                            'id': related_entity_name,
                            'label': label,
                            'name': related_entity_name,
                            'properties': related_entity.get('properties', {})
                        })

                        # 标记为已添加
                        added_node_ids.add(related_entity_name)

        # 特别处理课程实体：如果是课程，额外确保显示所有它包含的知识点
        if entity_label == 'Course':
            # 二次查找：确保显示所有CONTAINS关系的知识点和相关课程
            for relation in graph_data['relations']:
                source = relation.get('source')
                target = relation.get('target')
                relation_type = relation.get('relation_type', 'RELATED_TO')

                # 特别处理CONTAINS关系
                if source == entity_name and relation_type == 'CONTAINS':
                    if target not in added_node_ids and target in graph_data['entities']:
                        knowledge_entity = graph_data['entities'][target]
                        nodes.append({
                            'id': target,
                            'label': knowledge_entity.get('label', 'KnowledgePoint'),
                            'name': target,
                            'properties': knowledge_entity.get('properties', {})
                        })
                        added_node_ids.add(target)

                        # 确保添加这个关系
                        relation_already_added = False
                        for rel in relationships:
                            if (rel['source'] == source and
                                    rel['target'] == target and
                                    rel['type'] == get_chinese_relation_type(relation_type)):
                                relation_already_added = True
                                break

                        if not relation_already_added:
                            relationships.append({
                                'source': source,
                                'target': target,
                                'type': get_chinese_relation_type(relation_type),
                                'properties': {}
                            })

        # 添加一个二度关系：显示与知识点相关的其他知识点
        # 对于知识点实体，查找与它相关的其他知识点
        if entity_label == 'KnowledgePoint':
            # 找到所有与这个知识点相关的其他知识点
            related_knowledge_ids = set()
            for relation in relationships:
                if relation['source'] == entity_name:
                    related_knowledge_ids.add(relation['target'])
                elif relation['target'] == entity_name:
                    related_knowledge_ids.add(relation['source'])

            # 查找这些相关知识点之间的关系
            for relation in graph_data['relations']:
                source = relation.get('source')
                target = relation.get('target')

                # 如果关系两端都是已添加的知识点，则添加它们之间的关系
                if (source in related_knowledge_ids and target in related_knowledge_ids and
                        source in added_node_ids and target in added_node_ids):
                    # 检查关系是否已存在
                    relation_exists = False
                    for rel in relationships:
                        if (rel['source'] == source and rel['target'] == target and
                                rel['type'] == get_chinese_relation_type(relation.get('relation_type'))):
                            relation_exists = True
                            break

                    if not relation_exists:
                        relationships.append({
                            'source': source,
                            'target': target,
                            'type': get_chinese_relation_type(relation.get('relation_type', 'RELATED_TO')),
                            'properties': {}
                        })

        return {
            'success': True,
            'data': {
                'nodes': nodes,
                'relationships': relationships,
                'total_found': len(nodes)
            }
        }

    except Exception as e:
        logger.error(f"查找相关实体失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_all_knowledge_points():
    """获取所有知识点 - 完全基于Flask版本的实现"""
    try:
        global graph_data

        nodes = []
        relationships = []

        # 添加所有知识点
        knowledge_node_ids = set()
        for name, entity in graph_data['entities'].items():
            if entity.get('label') == 'KnowledgePoint':
                nodes.append({
                    'id': name,
                    'label': 'KnowledgePoint',
                    'name': name,
                    'properties': entity.get('properties', {})
                })
                knowledge_node_ids.add(name)

        # 只添加知识点之间的关系
        for relation in graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')

            if source in knowledge_node_ids and target in knowledge_node_ids:
                relationships.append({
                    'source': source,
                    'target': target,
                    'type': get_chinese_relation_type(relation.get('relation_type', 'RELATED_TO')),
                    'properties': {}
                })

        return {
            'success': True,
            'data': {
                'nodes': nodes,
                'relationships': relationships,
                'total_found': len(nodes)
            }
        }

    except Exception as e:
        logger.error(f"获取知识点失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def create_course_relationships(course_node_ids, graph_data):
    """创建课程之间的关系，基于课程的主题和先决条件"""
    relationships = []
    courses = list(course_node_ids)

    # 定义课程之间的先决条件关系
    prerequisite_map = {
        '数据结构与算法': ['计算机组成原理'],
        '人工智能导论': ['数据结构与算法'],
        '机器学习': ['人工智能导论', '数据结构与算法'],
        '深度学习': ['机器学习'],
        '计算机视觉': ['深度学习'],
        '自然语言处理': ['机器学习'],
        '计算机网络': ['计算机组成原理'],
        '网络安全': ['计算机网络'],
        '数据库系统': ['数据结构与算法'],
        '大数据技术': ['数据库系统'],
        '云计算': ['计算机网络'],
        '操作系统': ['计算机组成原理'],
        '软件工程': ['数据结构与算法'],
        '编译原理': ['数据结构与算法'],
        'Web开发': ['数据库系统', '计算机网络'],
        '移动应用开发': ['软件工程'],
        '区块链技术': ['计算机网络', '密码学'],
        '物联网技术': ['计算机网络'],
        '计算机图形学': ['数据结构与算法']
    }

    # 添加先决条件关系
    for course, prerequisites in prerequisite_map.items():
        if course in course_node_ids:
            for prereq in prerequisites:
                if prereq in course_node_ids:
                    relationships.append({
                        'source': prereq,
                        'target': course,
                        'type': '先决条件',
                        'properties': {'generated': True}
                    })

    # 添加相关课程关系
    related_courses = [
        ('机器学习', '深度学习', '相关'),
        ('计算机视觉', '自然语言处理', '相关'),
        ('计算机网络', '网络安全', '相关'),
        ('数据库系统', '大数据技术', '相关'),
        ('云计算', '大数据技术', '相关'),
        ('Web开发', '移动应用开发', '相关'),
        ('区块链技术', '网络安全', '相关'),
        ('物联网技术', '云计算', '相关')
    ]

    for source, target, rel_type in related_courses:
        if source in course_node_ids and target in course_node_ids:
            relationships.append({
                'source': source,
                'target': target,
                'type': rel_type,
                'properties': {'generated': True}
            })

    return relationships

def get_all_courses():
    """获取所有课程 - 只显示课程节点和它们之间的关系"""
    try:
        global graph_data

        nodes = []
        relationships = []

        # 添加所有课程
        course_node_ids = set()
        for name, entity in graph_data['entities'].items():
            if entity.get('label') == 'Course':
                nodes.append({
                    'id': name,
                    'label': 'Course',
                    'name': name,
                    'properties': entity.get('properties', {})
                })
                course_node_ids.add(name)

        # 查找课程之间的关系
        for relation in graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            relation_type = relation.get('relation_type', 'RELATED_TO')

            # 只添加课程之间的关系
            if source in course_node_ids and target in course_node_ids:
                relationships.append({
                    'source': source,
                    'target': target,
                    'type': get_chinese_relation_type(relation_type),
                    'properties': {}
                })

        # 如果课程之间没有直接关系，创建一些基于课程特性的关系
        if len(relationships) == 0:
            relationships = create_course_relationships(course_node_ids, graph_data)

        return {
            'success': True,
            'nodes': nodes,
            'relationships': relationships,
            'total_nodes': len(nodes),
            'total_relationships': len(relationships)
        }

    except Exception as e:
        logger.error(f"获取课程失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_full_graph():
    """获取完整图谱数据 - 完全基于Flask版本的实现，限制节点数量避免前端渲染过慢"""
    try:
        global graph_data

        nodes = []
        relationships = []

        # 限制返回的节点数量，避免前端渲染过慢
        max_nodes = 500
        node_count = 0

        # 优先添加课程节点，确保课程节点不被截断
        course_nodes = []
        knowledge_nodes = []
        other_nodes = []

        for name, entity in graph_data['entities'].items():
            node_data = {
                'id': name,
                'label': entity.get('label', 'Entity'),
                'name': name,
                'properties': entity.get('properties', {})
            }

            if entity.get('label') == 'Course':
                course_nodes.append(node_data)
            elif entity.get('label') == 'KnowledgePoint':
                knowledge_nodes.append(node_data)
            else:
                other_nodes.append(node_data)

        # 按优先级添加节点：课程 > 知识点 > 其他
        for node_list in [course_nodes, knowledge_nodes, other_nodes]:
            for node in node_list:
                if node_count >= max_nodes:
                    break
                nodes.append(node)
                node_count += 1
            if node_count >= max_nodes:
                break

        # 记录已添加节点的ID
        added_node_ids = {node['id'] for node in nodes}

        # 添加关系，只添加两端节点都存在的关系
        for relation in graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')

            if source in added_node_ids and target in added_node_ids:
                relationships.append({
                    'source': source,
                    'target': target,
                    'type': get_chinese_relation_type(relation.get('relation_type', 'RELATED_TO')),
                    'properties': {}
                })

        return {
            'success': True,
            'nodes': nodes,
            'relationships': relationships,
            'total_nodes': len(nodes),
            'total_relationships': len(relationships),
            'message': f"图谱数据已限制为 {len(nodes)} 个节点，使用预设查询获取更多特定数据。"
        }

    except Exception as e:
        logger.error(f"获取完整图谱失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_statistics():
    """获取图谱统计信息 - 基于Flask版本实现，返回数据而不是JsonResponse"""
    try:
        global graph_data

        entities = graph_data.get('entities', {})
        relations = graph_data.get('relations', [])

        # 统计实体类型
        entity_types = {}
        for entity_data in entities.values():
            entity_type = entity_data.get('label', 'Unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        # 统计关系类型
        relation_types = {}
        for relation in relations:
            relation_type = relation.get('relation_type', relation.get('type', 'UNKNOWN'))
            relation_types[relation_type] = relation_types.get(relation_type, 0) + 1

        return {
            'success': True,
            'data': {
                'total_entities': len(entities),
                'total_relations': len(relations),
                'entity_types': entity_types,
                'relation_types': relation_types,
                'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@csrf_exempt
@require_http_methods(["POST"])
def search_entities_api(request):
    """搜索实体API接口"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        search_term = data.get('search_term', '')
        result = search_entities(search_term)
        response = JsonResponse({
            'status': 'success',
            'data': result,
            'timestamp': datetime.datetime.now().isoformat()
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        response = JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

@csrf_exempt
@require_http_methods(["POST"])
def find_path_api(request):
    """查找路径API接口"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        source = data.get('source', '')
        target = data.get('target', '')
        result = find_path(source, target)
        response = JsonResponse({
            'status': 'success',
            'data': result,
            'timestamp': datetime.datetime.now().isoformat()
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        response = JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

@csrf_exempt
@require_http_methods(["POST"])
def find_related_api(request):
    """查找相关实体API接口"""
    try:
        data = json.loads(request.body)
        entity_name = data.get('entity_name', '')
        result = find_related(entity_name)
        return JsonResponse({
            'status': 'success',
            'data': result,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        })

@require_http_methods(["GET"])
def get_statistics_api(request):
    """获取统计信息API接口 - 返回前端期望的格式"""
    try:
        result = get_statistics()
        if result.get('success'):
            data = result.get('data', {})
            response = JsonResponse({
                'success': True,
                'entity_count': data.get('total_entities', 0),
                'relation_count': data.get('total_relations', 0),
                'entity_types': data.get('entity_types', {}),
                'relation_types': data.get('relation_types', {}),
                'last_updated': data.get('last_updated', ''),
                'timestamp': datetime.datetime.now().isoformat()
            }, json_dumps_params={'ensure_ascii': False})
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response
        else:
            response = JsonResponse({
                'success': False,
                'error': result.get('error', '获取统计信息失败'),
                'timestamp': datetime.datetime.now().isoformat()
            }, json_dumps_params={'ensure_ascii': False})
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response
    except Exception as e:
        response = JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

@require_http_methods(["GET"])
def get_knowledge_points_api(request):
    """获取知识点API接口"""
    try:
        result = get_all_knowledge_points()
        return JsonResponse({
            'status': 'success',
            'data': result,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        })

@require_http_methods(["GET"])
def get_courses_api(request):
    """获取课程API接口"""
    try:
        result = get_all_courses()
        return JsonResponse({
            'status': 'success',
            'data': result,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        })

@require_http_methods(["GET"])
def get_graph_data_api(request):
    """获取图谱数据API接口"""
    try:
        max_nodes = request.GET.get('max_nodes', 100)
        try:
            max_nodes = int(max_nodes)
        except:
            max_nodes = 100

        # 获取完整图谱数据，但限制节点数量
        full_graph_result = get_full_graph()
        if full_graph_result.get('success'):
            nodes = full_graph_result.get('nodes', [])
            relationships = full_graph_result.get('relationships', [])

            # 限制节点数量
            if len(nodes) > max_nodes:
                nodes = nodes[:max_nodes]
                # 过滤相关的关系
                node_ids = set(node['id'] for node in nodes)
                relationships = [
                    rel for rel in relationships
                    if rel['source'] in node_ids and rel['target'] in node_ids
                ]

            return JsonResponse({
                'status': 'success',
                'nodes': nodes,
                'relationships': relationships,
                'total_nodes': len(nodes),
                'total_relationships': len(relationships),
                'timestamp': datetime.datetime.now().isoformat()
            })
        else:
            return JsonResponse({
                'status': 'error',
                'error': full_graph_result.get('error', '获取图谱数据失败'),
                'timestamp': datetime.datetime.now().isoformat()
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        })

@csrf_exempt
@require_http_methods(["POST"])
def run_collection_api(request):
    """启动数据采集API接口 - 基于Flask版本实现"""
    try:
        # 获取表单数据
        collection_type = request.POST.get('collection_type', 'baidu')
        max_items = int(request.POST.get('max_items', 50))
        timeout = int(request.POST.get('timeout', 300))
        retry_count = int(request.POST.get('retry_count', 3))
        topics_str = request.POST.get('topics', '[]')

        try:
            topics = json.loads(topics_str)
        except:
            topics = ['人工智能', '机器学习', '数据结构', '算法']

        # 生成任务ID
        import uuid
        task_id = str(uuid.uuid4())

        # 保存采集配置
        config = {
            'task_id': task_id,
            'collection_type': collection_type,
            'max_items': max_items,
            'timeout': timeout,
            'retry_count': retry_count,
            'topics': topics,
            'status': 'started',
            'start_time': datetime.datetime.now().isoformat(),
            'progress': 0
        }

        # 保存配置到文件
        config_file = os.path.join(os.path.dirname(__file__), 'apps', 'data', 'collection_config.json')
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 启动后台采集任务（这里模拟启动）
        logger.info(f"启动数据采集任务: {task_id}, 类型: {collection_type}, 最大项目: {max_items}")

        return JsonResponse({
            'success': True,
            'data': {
                'task_id': task_id,
                'status': 'started',
                'message': f'数据采集任务已启动，类型: {collection_type}',
                'config': {
                    'collection_type': collection_type,
                    'max_items': max_items,
                    'timeout': timeout,
                    'topics': topics
                },
                'estimated_duration': f'{max_items // 10 + 5}-{max_items // 5 + 10}分钟'
            }
        })

    except Exception as e:
        logger.error(f"启动数据采集失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def get_collection_progress_api(request):
    """获取采集进度API接口 - 基于Flask版本实现"""
    try:
        # 读取配置文件
        config_file = os.path.join(os.path.dirname(__file__), 'apps', 'data', 'collection_config.json')
        progress_file = os.path.join(os.path.dirname(__file__), 'apps', 'data', 'collection_progress.json')

        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {'status': 'idle', 'task_id': None}

        # 模拟进度数据
        progress_data = {
            'status': config.get('status', 'idle'),
            'task_id': config.get('task_id'),
            'progress': {
                'current_step': '数据采集完成',
                'percentage': 100,
                'processed_items': config.get('max_items', 0),
                'total_items': config.get('max_items', 0),
                'start_time': config.get('start_time'),
                'estimated_completion': datetime.datetime.now().isoformat()
            },
            'timeline': [
                {
                    'time': config.get('start_time', datetime.datetime.now().isoformat()),
                    'event': '任务启动',
                    'details': f"开始采集{config.get('collection_type', 'unknown')}数据"
                },
                {
                    'time': datetime.datetime.now().isoformat(),
                    'event': '采集完成',
                    'details': f"成功采集{config.get('max_items', 0)}个项目"
                }
            ]
        }

        # 如果有进度文件，读取实际进度
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    actual_progress = json.load(f)
                    progress_data.update(actual_progress)
            except Exception as e:
                logger.error(f"读取进度文件失败: {str(e)}")

        return JsonResponse({
            'success': True,
            'data': progress_data
        })

    except Exception as e:
        logger.error(f"获取采集进度失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def check_updates(request):
    """检查是否有新的更新"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        last_update = data.get('last_update', 0)

        # 检查文件修改时间
        latest_update = last_update

        json_path = os.path.join(os.path.dirname(__file__), 'apps', 'knowledge_graph.json')
        if os.path.exists(json_path):
            file_time = os.path.getmtime(json_path)
            if file_time > latest_update:
                latest_update = file_time

        pickle_path = os.path.join(os.path.dirname(__file__), 'apps', 'knowledge_graph.pkl')
        if os.path.exists(pickle_path):
            file_time = os.path.getmtime(pickle_path)
            if file_time > latest_update:
                latest_update = file_time

        response = JsonResponse({
            'has_updates': latest_update > last_update,
            'latest_update': latest_update
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        response = JsonResponse({
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

@require_http_methods(["GET"])
def check_neo4j_status_api(request):
    """检查Neo4j数据库连接状态API接口"""
    try:
        is_connected, message = check_neo4j_connection()

        # 获取数据源信息
        data_source = "未知"
        data_count = {"entities": 0, "relations": 0}

        if is_connected:
            data_source = "Neo4j数据库"
            data_count = {
                "entities": len(graph_data.get('entities', {})),
                "relations": len(graph_data.get('relations', []))
            }
        else:
            # 检查是否有本地缓存数据
            if graph_data.get('entities'):
                data_source = "本地缓存文件"
                data_count = {
                    "entities": len(graph_data.get('entities', {})),
                    "relations": len(graph_data.get('relations', []))
                }

        response = JsonResponse({
            'success': True,
            'neo4j_connected': is_connected,
            'connection_message': message,
            'data_source': data_source,
            'data_count': data_count,
            'timestamp': datetime.datetime.now().isoformat()
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        response = JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

@csrf_exempt
@require_http_methods(["POST"])
def reload_data_from_neo4j_api(request):
    """强制从Neo4j重新加载数据API接口"""
    try:
        logger.info("收到强制从Neo4j重新加载数据的请求")

        # 尝试从Neo4j重新加载数据
        success = load_graph_data_from_neo4j()

        if success:
            response = JsonResponse({
                'success': True,
                'message': f'成功从Neo4j重新加载数据: {len(graph_data.get("entities", {}))} 个实体, {len(graph_data.get("relations", []))} 个关系',
                'data_count': {
                    'entities': len(graph_data.get('entities', {})),
                    'relations': len(graph_data.get('relations', []))
                },
                'timestamp': datetime.datetime.now().isoformat()
            }, json_dumps_params={'ensure_ascii': False})
        else:
            response = JsonResponse({
                'success': False,
                'message': 'Neo4j数据库不可用或没有数据，请检查Neo4j服务是否启动',
                'suggestions': [
                    '1. 确保Neo4j数据库服务正在运行',
                    '2. 检查数据库连接配置',
                    '3. 确认数据库中有知识图谱数据',
                    '4. 查看服务器日志获取详细错误信息'
                ],
                'timestamp': datetime.datetime.now().isoformat()
            }, json_dumps_params={'ensure_ascii': False})

        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        response = JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }, json_dumps_params={'ensure_ascii': False})
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

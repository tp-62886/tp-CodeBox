from flask import Flask, render_template, request, jsonify
from neo4j_connector import Neo4j
from nlp_converter import NLPCypherConverter
import os
from dotenv import find_dotenv, load_dotenv
import json
import pickle
import time
import shutil
import asyncio
import threading
import datetime

# 创建关系类型的中英文映射
RELATION_TYPES_MAP = {
    'CONTAINS': '包含',
    'RELATED_TO': '相关于',
    'PREREQUISITE': '先修于',
    'PREREQUISITE_FOR': '后续',
    'SIMILAR_TO': '相似于'
}


# 将关系类型转换为中文
def get_chinese_relation_type(relation_type):
    """将英文关系类型转换为中文显示"""
    return RELATION_TYPES_MAP.get(relation_type, relation_type)


# 尝试加载环境变量
try:
    load_dotenv(find_dotenv())
except Exception:
    pass

app = Flask(__name__)

# 初始化Neo4j连接
neo4j = Neo4j(
    uri=os.getenv("NEO4J_URI"),
    user=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD")
)

# 初始化NLP转换器
converter = NLPCypherConverter()

# 初始化全局变量存储知识图谱数据
graph_data = {
    'entities': {},
    'relations': []
}


def load_graph_data():
    """加载知识图谱数据"""
    global graph_data

    print("加载知识图谱数据...")

    # 先尝试从pickle文件加载（更快）
    if os.path.exists('knowledge_graph.pkl'):
        try:
            with open('knowledge_graph.pkl', 'rb') as f:
                data = pickle.load(f)
                graph_data = data
                print(
                    f"从pickle文件加载了知识图谱数据: {len(graph_data.get('entities', {}))} 个实体, {len(graph_data.get('relations', []))} 个关系")
                return True
        except Exception as e:
            print(f"从pickle文件加载失败: {str(e)}")

    # 再尝试从JSON文件加载
    if os.path.exists('knowledge_graph.json'):
        try:
            with open('knowledge_graph.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                graph_data = data
                print(
                    f"从JSON文件加载了知识图谱数据: {len(graph_data.get('entities', {}))} 个实体, {len(graph_data.get('relations', []))} 个关系")
                return True
        except Exception as e:
            print(f"从JSON文件加载失败: {str(e)}")

    # 尝试从已收集的数据文件加载
    if os.path.exists('data/collected_knowledge.json'):
        try:
            print("尝试从已收集的知识点数据构建图谱数据...")
            with open('data/collected_knowledge.json', 'r', encoding='utf-8') as f:
                collected_data = json.load(f)

                # 构建图谱数据结构
                temp_graph_data = {
                    'entities': {},
                    'relations': []
                }

                # 处理收集到的数据
                for item in collected_data:
                    if item.get('type') == 'entity' and 'name' in item:
                        temp_graph_data['entities'][item['name']] = item
                    elif item.get('type') == 'relation':
                        temp_graph_data['relations'].append(item)

                # 更新全局变量
                graph_data = temp_graph_data
                print(
                    f"从collected_knowledge.json构建了图谱数据: {len(graph_data.get('entities', {}))} 个实体, {len(graph_data.get('relations', []))} 个关系")

                # 保存为标准格式，便于下次使用
                try:
                    with open('knowledge_graph.json', 'w', encoding='utf-8') as f:
                        json.dump(graph_data, f, ensure_ascii=False, indent=2)
                    print("知识图谱数据已保存为标准格式")
                except Exception as e:
                    print(f"保存标准格式失败: {str(e)}")

                return True
        except Exception as e:
            print(f"从collected_knowledge.json加载失败: {str(e)}")

    # 如果所有加载方式都失败，返回空数据结构
    print("所有加载方式都失败，使用空数据结构")
    graph_data = {
        'entities': {},
        'relations': []
    }
    return False


# 在应用启动时加载数据
load_graph_data()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/query', methods=['POST'])
def query():
    """处理查询请求"""
    try:
        query_text = request.json.get('query', '')

        # 解析查询内容
        if 'search' in query_text.lower():
            # 搜索实体
            search_term = query_text.lower().replace('search', '').strip()
            return search_entities(search_term)
        elif 'path' in query_text.lower():
            # 查找路径
            parts = query_text.split()
            if len(parts) >= 3:
                source = parts[-2]
                target = parts[-1]
                return find_path(source, target)
        elif 'related' in query_text.lower():
            # 查找相关实体
            entity_name = query_text.lower().replace('related', '').strip()
            return find_related(entity_name)
        elif ('知识点' in query_text.lower() or
              'knowledge' in query_text.lower() or
              'point' in query_text.lower()):
            # 返回所有知识点
            return get_all_knowledge_points()
        elif ('课程' in query_text.lower() or
              'course' in query_text.lower()):
            # 返回所有课程
            return get_all_courses()
        elif '整个' in query_text.lower() or '全部' in query_text.lower():
            # 返回整个图谱
            return get_full_graph()
        else:
            # 默认返回整个图谱
            return get_full_graph()

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


def search_entities(search_term):
    """搜索实体"""
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
        from save_graph import CORE_KNOWLEDGE_POINTS
        for name in CORE_KNOWLEDGE_POINTS:
            if name in graph_data['entities']:
                matching_entities.append(graph_data['entities'][name])
                print(f"未找到匹配，返回核心知识点: {name}")
                break

    # 最后的保险措施 - 如果实在找不到任何匹配，返回错误信息
    if not matching_entities:
        return jsonify({
            'success': False,
            'error': f"没有找到与 '{search_term}' 匹配的实体"
        })

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

    # 特别处理课程实体：如果是课程，确保显示所有它包含的知识点
    for entity in matching_entities:
        entity_name = entity.get('name')
        entity_label = entity.get('label')

        if entity_label == 'Course':
            # 查找该课程包含的所有知识点（即使在上面的步骤中未找到）
            for relation in graph_data['relations']:
                source = relation.get('source')
                target = relation.get('target')
                relation_type = relation.get('relation_type')

                # 找出课程CONTAINS知识点的所有关系
                if (source == entity_name and relation_type == 'CONTAINS'):
                    # 如果目标知识点尚未添加到节点列表
                    if target not in added_node_ids and target in graph_data['entities']:
                        knowledge_entity = graph_data['entities'][target]
                        nodes.append({
                            'id': target,
                            'label': knowledge_entity.get('label', 'KnowledgePoint'),
                            'name': target,
                            'properties': knowledge_entity.get('properties', {})
                        })
                        added_node_ids.add(target)

                    # 添加CONTAINS关系（如果尚未添加）
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

    return jsonify({
        'success': True,
        'nodes': nodes,
        'relationships': relationships,
        'cypher_query': f"搜索实体: {search_term}"
    })


def find_path(source, target):
    """查找两个实体之间的路径"""
    # 检查源和目标实体是否存在
    if source not in graph_data['entities']:
        return jsonify({
            'success': False,
            'error': f"源实体不存在: {source}"
        })

    if target not in graph_data['entities']:
        return jsonify({
            'success': False,
            'error': f"目标实体不存在: {target}"
        })

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

            return jsonify({
                'success': True,
                'nodes': nodes,
                'relationships': relationships,
                'path_length': len(path),
                'cypher_query': f"从 {source} 到 {target} 的路径"
            })

        # 继续BFS搜索
        for neighbor, rel_type in graph.get(current, []):
            if neighbor not in visited:
                visited[neighbor] = current
                queue.append((neighbor, path + [(current, rel_type)]))

    # 没有找到路径
    return jsonify({
        'success': False,
        'error': f"未找到从 {source} 到 {target} 的路径"
    })


def find_related(entity_name):
    """查找与指定实体相关的实体"""
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
            return jsonify({
                'success': False,
                'error': f"未找到实体: {entity_name}"
            })

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

    return jsonify({
        'success': True,
        'nodes': nodes,
        'relationships': relationships,
        'cypher_query': f"与 {entity_name} 相关的实体"
    })


def get_all_knowledge_points():
    """获取所有知识点"""
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

    # 只添加知识点之间的关系，不添加与课程的关系
    for relation in graph_data['relations']:
        source = relation.get('source')
        target = relation.get('target')

        # 确保关系两端都是知识点
        if (source in knowledge_node_ids and target in knowledge_node_ids):
            relationships.append({
                'source': source,
                'target': target,
                'type': get_chinese_relation_type(relation.get('relation_type', 'RELATED_TO')),
                'properties': {}
            })

    return jsonify({
        'success': True,
        'nodes': nodes,
        'relationships': relationships,
        'cypher_query': "所有知识点"
    })


def get_all_courses():
    """获取所有课程"""
    nodes = []
    relationships = []

    # 添加所有课程节点
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

    # 只添加课程之间的关系，不添加与知识点的关系
    for relation in graph_data['relations']:
        source = relation.get('source')
        target = relation.get('target')

        # 确保关系两端都是课程
        if source in course_node_ids and target in course_node_ids:
            relationships.append({
                'source': source,
                'target': target,
                'type': get_chinese_relation_type(relation.get('relation_type', 'RELATED_TO')),
                'properties': {}
            })

    return jsonify({
        'success': True,
        'nodes': nodes,
        'relationships': relationships,
        'cypher_query': "所有课程"
    })


def get_full_graph():
    """获取完整的图谱"""
    nodes = []
    relationships = []

    # 添加所有实体
    for name, entity in graph_data['entities'].items():
        nodes.append({
            'id': name,
            'label': entity.get('label', 'Entity'),
            'name': name,
            'properties': entity.get('properties', {})
        })

    # 添加所有关系
    for relation in graph_data['relations']:
        source = relation.get('source')
        target = relation.get('target')

        # 确保关系两端的实体都存在
        if source in graph_data['entities'] and target in graph_data['entities']:
            relationships.append({
                'source': source,
                'target': target,
                'type': get_chinese_relation_type(relation.get('relation_type', 'RELATED_TO')),
                'properties': {}
            })

    return jsonify({
        'success': True,
        'nodes': nodes,
        'relationships': relationships,
        'cypher_query': "完整知识图谱"
    })


@app.route('/get_graph_data')
def get_graph_data():
    """获取最新的图谱数据"""
    try:
        # 重新加载数据（以防数据已更新）
        load_graph_data()

        # 检查数据大小，如果实体太多，可能需要限制返回数量
        entity_count = len(graph_data['entities'])
        relation_count = len(graph_data['relations'])

        print(f"获取图谱数据: {entity_count} 个实体, {relation_count} 个关系")

        # 如果实体数量太多，只返回部分（默认限制为100个实体）
        max_entities = 100
        if entity_count > max_entities:
            print(f"实体数量超过限制，返回部分数据（最多{max_entities}个实体）")
            # 使用有限的数据创建子图
            return get_limited_graph_data(max_entities)

        # 转换为节点和关系列表
        nodes = []
        for name, entity in graph_data['entities'].items():
            nodes.append({
                'id': name,
                'label': entity.get('label', 'Entity'),
                'name': name,
                'properties': entity.get('properties', {})
            })

        # 创建实体名称到标签的映射，用于检查实体类型
        entity_name_to_label = {}
        for name, entity in graph_data['entities'].items():
            entity_name_to_label[name] = entity.get('label', '')

        relationships = []
        for relation in graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            relation_type = relation.get('relation_type', 'RELATED_TO')

            # 确保关系两端的实体都存在
            if source in graph_data['entities'] and target in graph_data['entities']:
                # 跳过课程-课程的CONTAINS关系
                if relation_type == 'CONTAINS':
                    source_label = entity_name_to_label.get(source)
                    target_label = entity_name_to_label.get(target)

                    # 如果源和目标都是课程，不添加这个CONTAINS关系
                    if source_label == 'Course' and target_label == 'Course':
                        continue

                relationships.append({
                    'source': source,
                    'target': target,
                    'type': get_chinese_relation_type(relation_type),
                    'properties': {}
                })

        return jsonify({
            'success': True,
            'nodes': nodes,
            'relationships': relationships
        })
    except Exception as e:
        print(f"获取图谱数据错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_limited_graph_data(limit=100):
    """获取有限数量的图谱数据"""
    # 优先选择课程实体
    course_entities = {}
    knowledge_entities = {}

    for name, entity in graph_data['entities'].items():
        if entity.get('label') == 'Course':
            course_entities[name] = entity
        elif entity.get('label') == 'KnowledgePoint':
            knowledge_entities[name] = entity

    # 创建有限的节点列表
    nodes = []
    node_ids = set()

    # 首先添加所有课程
    for name, entity in course_entities.items():
        nodes.append({
            'id': name,
            'label': 'Course',
            'name': name,
            'properties': entity.get('properties', {})
        })
        node_ids.add(name)

        # 如果已达到限制，停止添加
        if len(nodes) >= limit:
            break

    # 如果还有空间，添加一些知识点
    remaining_slots = limit - len(nodes)
    if remaining_slots > 0:
        # 只添加部分知识点
        knowledge_sample = list(knowledge_entities.items())[:remaining_slots]
        for name, entity in knowledge_sample:
            nodes.append({
                'id': name,
                'label': 'KnowledgePoint',
                'name': name,
                'properties': entity.get('properties', {})
            })
            node_ids.add(name)

    # 创建实体名称到标签的映射，用于检查实体类型
    entity_name_to_label = {}
    for node in nodes:
        entity_name_to_label[node['id']] = node['label']

    # 创建关系列表（只包含已添加节点之间的关系）
    relationships = []
    for relation in graph_data['relations']:
        source = relation.get('source')
        target = relation.get('target')
        relation_type = relation.get('relation_type', 'RELATED_TO')

        # 确保关系两端的实体都在节点列表中
        if source in node_ids and target in node_ids:
            # 跳过课程-课程的CONTAINS关系
            if relation_type == 'CONTAINS':
                source_label = entity_name_to_label.get(source)
                target_label = entity_name_to_label.get(target)

                # 如果源和目标都是课程，不添加这个CONTAINS关系
                if source_label == 'Course' and target_label == 'Course':
                    continue

            relationships.append({
                'source': source,
                'target': target,
                'type': get_chinese_relation_type(relation_type),
                'properties': {}
            })

    return jsonify({
        'success': True,
        'nodes': nodes,
        'relationships': relationships,
        'limited': True,
        'total_entities': len(graph_data['entities']),
        'total_relations': len(graph_data['relations']),
        'message': f"图谱数据已限制为 {len(nodes)} 个节点，使用预设查询获取更多特定数据。"
    })


@app.route('/check_updates', methods=['POST'])
def check_updates():
    """检查是否有新的更新"""
    try:
        data = request.get_json()
        last_update = data.get('last_update', 0)

        # 检查文件修改时间
        latest_update = last_update

        if os.path.exists('knowledge_graph.json'):
            file_time = os.path.getmtime('knowledge_graph.json')
            if file_time > latest_update:
                latest_update = file_time

        if os.path.exists('knowledge_graph.pkl'):
            file_time = os.path.getmtime('knowledge_graph.pkl')
            if file_time > latest_update:
                latest_update = file_time

        if os.path.exists('data/collected_knowledge.json'):
            file_time = os.path.getmtime('data/collected_knowledge.json')
            if file_time > latest_update:
                latest_update = file_time

        return jsonify({
            'has_updates': latest_update > last_update,
            'latest_update': latest_update
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/statistics')
def statistics():
    """获取知识图谱统计信息"""
    try:
        # 统计实体类型分布
        entity_types = {}
        for entity in graph_data['entities'].values():
            label = entity.get('label', 'Unknown')
            if label in entity_types:
                entity_types[label] += 1
            else:
                entity_types[label] = 1

        # 统计关系类型分布
        relation_types = {}
        for relation in graph_data['relations']:
            rel_type = relation.get('relation_type', 'Unknown')
            # 使用中文显示关系类型
            chinese_rel_type = get_chinese_relation_type(rel_type)
            if chinese_rel_type in relation_types:
                relation_types[chinese_rel_type] += 1
            else:
                relation_types[chinese_rel_type] = 1

        return jsonify({
            'success': True,
            'entity_count': len(graph_data['entities']),
            'relation_count': len(graph_data['relations']),
            'entity_types': entity_types,
            'relation_types': relation_types
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin')
def admin_panel():
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
        if os.path.exists('data/collection_progress.json'):
            with open('data/collection_progress.json', 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                progress_info['last_batch'] = progress_data.get('last_batch', 0)
                progress_info['total_batches'] = progress_data.get('total_batches', 0)
                progress_info['last_updated'] = progress_data.get('last_updated', '未知')
                progress_info['processed_topics'] = progress_data.get('processed_topics', [])
    except Exception as e:
        print(f"读取采集进度失败: {str(e)}")

    return render_template('admin.html', progress=progress_info)


@app.route('/run_collection', methods=['POST'])
def run_collection():
    """执行知识点采集任务"""
    try:
        collection_type = request.form.get('collection_type', 'continue')

        # 构建命令
        if collection_type == 'reset':
            cmd = ['python', 'run.py', '--reset']
        elif collection_type == 'continue':
            cmd = ['python', 'run.py', '--continue-collection']
        else:
            cmd = ['python', 'run.py']  # 默认执行

        # 使用子进程执行命令
        import subprocess
        import os
        import sys

        # 创建进度文件目录（如果不存在）
        os.makedirs('data', exist_ok=True)

        # 记录开始采集的信息到进度文件
        progress_file = 'data/collection_progress.json'
        progress_info = {
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'running',
            'collection_type': collection_type
        }

        # 读取已有进度信息（如果存在）
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    existing_progress = json.load(f)
                    # 保留一些重要的历史信息
                    if 'processed_topics' in existing_progress:
                        progress_info['processed_topics'] = existing_progress['processed_topics']
                    if 'last_batch' in existing_progress and collection_type != 'reset':
                        progress_info['last_batch'] = existing_progress['last_batch']
                    if 'total_batches' in existing_progress and collection_type != 'reset':
                        progress_info['total_batches'] = existing_progress['total_batches']
            except Exception as e:
                print(f"读取进度文件失败: {str(e)}")

        # 更新进度文件
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_info, f, ensure_ascii=False, indent=2)

        # 获取当前Python解释器路径，确保使用相同的解释器运行脚本
        python_exe = sys.executable or 'python'
        if python_exe != 'python':
            cmd[0] = python_exe

        # 构建命令并添加必要的参数
        if sys.platform == 'win32':  # Windows
            # 使用subprocess.Popen而不是os.system
            # 使用DETACHED_PROCESS标志让进程在后台运行
            try:
                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                    close_fds=True,
                    shell=False,  # 不使用shell，避免命令注入风险
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"在Windows上启动进程: {cmd}")
            except Exception as e:
                # 如果上面的方法失败，尝试备用方法
                print(f"启动失败，尝试备用方法: {str(e)}")
                # 使用startupinfo隐藏命令窗口
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                process = subprocess.Popen(
                    cmd,
                    startupinfo=startupinfo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False
                )
        else:  # Linux/Mac
            # 使用nohup确保进程在后台运行，即使终端关闭
            try:
                process = subprocess.Popen(
                    ['nohup'] + cmd + ['&'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None,  # 在新进程组中运行，如果支持的话
                    shell=False
                )
            except Exception as e:
                print(f"Linux启动失败，尝试备用方法: {str(e)}")
                # 备用方法，不使用preexec_fn
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False
                )

        # 记录启动信息
        with open('data/collection_run.log', 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 启动采集任务: {collection_type}, 命令: {' '.join(cmd)}\n")

        return jsonify({
            'success': True,
            'message': f"已启动采集任务，类型: {collection_type}。采集将在后台继续，您可以关闭浏览器。"
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"启动采集任务错误: {str(e)}\n{error_trace}")

        # 记录错误信息到日志
        try:
            with open('data/collection_error.log', 'a', encoding='utf-8') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误: {str(e)}\n{error_trace}\n")
        except:
            pass

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/get_collection_progress')
def get_collection_progress():
    """获取知识图谱采集进度"""
    try:
        # 读取进度文件
        progress_info = {
            'last_batch': 0,
            'total_batches': 0,
            'last_updated': '未知',
            'processed_topics': [],
            'status': 'idle'
        }

        if os.path.exists('data/collection_progress.json'):
            with open('data/collection_progress.json', 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                for key in progress_data:
                    progress_info[key] = progress_data[key]

                # 检查采集是否正在进行中
                if progress_info.get('status') == 'running':
                    # 检查上次更新时间是否超过10分钟
                    if 'last_updated' in progress_info:
                        try:
                            last_update_time = datetime.datetime.strptime(
                                progress_info['last_updated'],
                                '%Y-%m-%d %H:%M:%S'
                            )
                            now = datetime.datetime.now()
                            # 如果超过10分钟未更新，认为采集过程已停止
                            if (now - last_update_time).total_seconds() > 600:
                                progress_info['status'] = 'completed'
                                # 更新进度文件
                                with open('data/collection_progress.json', 'w', encoding='utf-8') as f:
                                    json.dump(progress_info, f, ensure_ascii=False, indent=2)
                        except Exception as e:
                            print(f"解析时间失败: {str(e)}")

        return jsonify({
            'success': True,
            'progress': progress_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
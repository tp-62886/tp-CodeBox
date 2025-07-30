# knowledgeGraph/knowledgeGraph_api.py
"""
知识图谱API接口文件
供前端调用的统一API接口
"""
import os
import json
import time
import logging
from collections import deque

# 导入业务逻辑模块
try:
    from .neo4j_connector import Neo4j
    from .nlp_converter import NLPCypherConverter
    from .save_graph import CORE_KNOWLEDGE_POINTS
except ImportError as e:
    print(f"导入Graphapps模块失败: {e}")
    Neo4j = None
    NLPCypherConverter = None
    CORE_KNOWLEDGE_POINTS = []

logger = logging.getLogger(__name__)

class KnowledgeGraphAPI:
    """知识图谱API类"""
    
    def __init__(self):
        # 初始化Neo4j连接
        try:
            if Neo4j:
                self.neo4j = Neo4j(
                    uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                    user=os.getenv("NEO4J_USER", "neo4j"),
                    password=os.getenv("NEO4J_PASSWORD", "12345678")
                )
            else:
                self.neo4j = None
        except Exception as e:
            logger.error(f"Neo4j连接失败: {str(e)}")
            self.neo4j = None
        
        # 初始化NLP转换器
        try:
            if NLPCypherConverter:
                self.converter = NLPCypherConverter()
            else:
                self.converter = None
        except Exception as e:
            logger.error(f"NLP转换器初始化失败: {str(e)}")
            self.converter = None
        
        # 初始化图谱数据
        self.graph_data = {
            'entities': {},
            'relations': []
        }
        self.load_graph_data()
    
    def get_data_file_path(self, filename):
        """获取数据文件的绝对路径"""
        base_dir = os.path.dirname(__file__)
        return os.path.join(base_dir, 'data', filename)
    
    def load_graph_data(self):
        """加载知识图谱数据"""
        # 尝试从pickle文件加载
        pickle_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.pkl')
        if os.path.exists(pickle_path):
            try:
                import pickle
                with open(pickle_path, 'rb') as f:
                    self.graph_data = pickle.load(f)
                    logger.info(f"从pickle文件加载了图谱数据: {len(self.graph_data.get('entities', {}))} 个实体")
                    return True
            except Exception as e:
                logger.error(f"从pickle文件加载失败: {str(e)}")
        
        # 尝试从JSON文件加载
        json_path = os.path.join(os.path.dirname(__file__), 'knowledge_graph.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.graph_data = json.load(f)
                    logger.info(f"从JSON文件加载了图谱数据: {len(self.graph_data.get('entities', {}))} 个实体")
                    return True
            except Exception as e:
                logger.error(f"从JSON文件加载失败: {str(e)}")
        
        # 尝试从已收集的数据文件加载
        collected_path = self.get_data_file_path('collected_knowledge.json')
        if os.path.exists(collected_path):
            try:
                with open(collected_path, 'r', encoding='utf-8') as f:
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
                    
                    # 更新数据
                    self.graph_data = temp_graph_data
                    logger.info(f"从collected_knowledge.json构建了图谱数据: {len(self.graph_data.get('entities', {}))} 个实体")
                    return True
            except Exception as e:
                logger.error(f"从collected_knowledge.json加载失败: {str(e)}")
        
        # 如果所有加载方式都失败，返回空数据结构
        logger.warning("所有加载方式都失败，使用空数据结构")
        self.graph_data = {
            'entities': {},
            'relations': []
        }
        return False
    
    def search_entities(self, search_term):
        """搜索实体"""
        nodes = []
        relationships = []
        
        # 核心知识点列表
        core_entities = ['算法', '数据结构', '人工智能', '机器学习', '深度学习', 
                        '计算机网络', '操作系统', '数据库', '软件工程', '编译原理']
        
        # 尝试精确匹配
        exact_matches = []
        for name, entity in self.graph_data['entities'].items():
            if search_term.lower() == name.lower():
                exact_matches.append(entity)
        
        # 如果有精确匹配，优先使用
        matching_entities = exact_matches if exact_matches else []
        
        # 如果没有精确匹配，尝试模糊匹配
        if not matching_entities:
            for name, entity in self.graph_data['entities'].items():
                if search_term.lower() in name.lower():
                    matching_entities.append(entity)
        
        # 如果仍然没有匹配，尝试部分词匹配
        if not matching_entities:
            search_words = search_term.lower().split()
            for name, entity in self.graph_data['entities'].items():
                name_lower = name.lower()
                for word in search_words:
                    if len(word) >= 2 and word in name_lower:
                        matching_entities.append(entity)
                        break
        
        # 如果仍然没有匹配，返回核心知识点
        if not matching_entities:
            for name in CORE_KNOWLEDGE_POINTS:
                if name in self.graph_data['entities']:
                    matching_entities.append(self.graph_data['entities'][name])
                    break
        
        # 构建返回数据
        added_node_ids = set()
        
        # 添加匹配的实体
        for entity in matching_entities[:10]:  # 限制返回数量
            entity_name = entity.get('name')
            if entity_name and entity_name not in added_node_ids:
                nodes.append({
                    'id': entity_name,
                    'label': entity.get('label', 'Entity'),
                    'name': entity_name,
                    'properties': entity.get('properties', {})
                })
                added_node_ids.add(entity_name)
        
        # 添加相关关系
        for relation in self.graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            
            if source in added_node_ids and target in added_node_ids:
                relationships.append({
                    'source': source,
                    'target': target,
                    'type': relation.get('relation_type', 'RELATED_TO'),
                    'properties': {}
                })
        
        return {
            'success': True,
            'nodes': nodes,
            'relationships': relationships,
            'query': f"搜索: {search_term}"
        }
    
    def get_graph_data(self, max_nodes=500):
        """获取图谱数据"""
        # 重新加载数据
        self.load_graph_data()
        
        nodes = []
        relationships = []
        
        # 限制返回的节点数量
        node_count = 0
        
        # 添加实体节点
        for name, entity in self.graph_data['entities'].items():
            if node_count >= max_nodes:
                break
            nodes.append({
                'id': name,
                'label': entity.get('label', 'Entity'),
                'name': name,
                'properties': entity.get('properties', {})
            })
            node_count += 1
        
        # 记录已添加节点的ID
        added_node_ids = {node['id'] for node in nodes}
        
        # 添加关系
        for relation in self.graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            
            if source in added_node_ids and target in added_node_ids:
                relationships.append({
                    'source': source,
                    'target': target,
                    'type': relation.get('relation_type', 'RELATED_TO'),
                    'properties': {}
                })
        
        return {
            'success': True,
            'nodes': nodes,
            'relationships': relationships,
            'total_entities': len(self.graph_data['entities']),
            'total_relations': len(self.graph_data['relations']),
            'message': f"图谱数据已限制为 {len(nodes)} 个节点"
        }
    
    def get_statistics(self):
        """获取统计信息"""
        # 统计实体类型分布
        entity_types = {}
        for name, entity in self.graph_data['entities'].items():
            entity_type = entity.get('label', 'Unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        # 统计关系类型分布
        relation_types = {}
        for relation in self.graph_data['relations']:
            relation_type = relation.get('relation_type', 'Unknown')
            relation_types[relation_type] = relation_types.get(relation_type, 0) + 1
        
        return {
            'success': True,
            'total_entities': len(self.graph_data['entities']),
            'total_relations': len(self.graph_data['relations']),
            'entity_types': entity_types,
            'relation_types': relation_types
        }
    
    def get_knowledge_points(self):
        """获取所有知识点"""
        nodes = []
        relationships = []
        
        # 添加所有知识点
        knowledge_node_ids = set()
        for name, entity in self.graph_data['entities'].items():
            if entity.get('label') == 'KnowledgePoint':
                nodes.append({
                    'id': name,
                    'label': 'KnowledgePoint',
                    'name': name,
                    'properties': entity.get('properties', {})
                })
                knowledge_node_ids.add(name)
        
        # 只添加知识点之间的关系
        for relation in self.graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            
            if source in knowledge_node_ids and target in knowledge_node_ids:
                relationships.append({
                    'source': source,
                    'target': target,
                    'type': relation.get('relation_type', 'RELATED_TO'),
                    'properties': {}
                })
        
        return {
            'success': True,
            'nodes': nodes,
            'relationships': relationships,
            'query': "所有知识点"
        }
    
    def get_courses(self):
        """获取所有课程"""
        nodes = []
        relationships = []
        
        # 添加所有课程
        course_node_ids = set()
        for name, entity in self.graph_data['entities'].items():
            if entity.get('label') == 'Course':
                nodes.append({
                    'id': name,
                    'label': 'Course',
                    'name': name,
                    'properties': entity.get('properties', {})
                })
                course_node_ids.add(name)
        
        # 添加课程之间的关系
        for relation in self.graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            
            if source in course_node_ids and target in course_node_ids:
                relationships.append({
                    'source': source,
                    'target': target,
                    'type': relation.get('relation_type', 'RELATED_TO'),
                    'properties': {}
                })
        
        return {
            'success': True,
            'nodes': nodes,
            'relationships': relationships,
            'query': "所有课程"
        }
    
    def find_path(self, source, target):
        """查找两个实体之间的路径"""
        # 检查源和目标实体是否存在
        if source not in self.graph_data['entities']:
            return {
                'success': False,
                'error': f"源实体不存在: {source}"
            }
        
        if target not in self.graph_data['entities']:
            return {
                'success': False,
                'error': f"目标实体不存在: {target}"
            }
        
        # 构建图结构
        graph = {}
        for entity_name in self.graph_data['entities']:
            graph[entity_name] = []
            
        for relation in self.graph_data['relations']:
            source_name = relation.get('source')
            target_name = relation.get('target')
            relation_type = relation.get('relation_type')
            
            if source_name in graph and target_name in graph:
                graph[source_name].append((target_name, relation_type))
                # 对于RELATED_TO关系，考虑双向
                if relation_type == 'RELATED_TO':
                    graph[target_name].append((source_name, relation_type))
        
        # 使用BFS查找最短路径
        queue = deque([(source, [source])])
        visited = {source}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target:
                # 找到路径，构建返回数据
                nodes = []
                relationships = []
                
                # 添加路径上的节点
                for node_name in path:
                    entity = self.graph_data['entities'][node_name]
                    nodes.append({
                        'id': node_name,
                        'label': entity.get('label', 'Entity'),
                        'name': node_name,
                        'properties': entity.get('properties', {})
                    })
                
                # 添加路径上的关系
                for i in range(len(path) - 1):
                    source_node = path[i]
                    target_node = path[i + 1]
                    
                    # 查找对应的关系
                    for relation in self.graph_data['relations']:
                        if (relation.get('source') == source_node and 
                            relation.get('target') == target_node) or \
                           (relation.get('relation_type') == 'RELATED_TO' and
                            relation.get('source') == target_node and 
                            relation.get('target') == source_node):
                            relationships.append({
                                'source': source_node,
                                'target': target_node,
                                'type': relation.get('relation_type', 'RELATED_TO'),
                                'properties': {}
                            })
                            break
                
                return {
                    'success': True,
                    'nodes': nodes,
                    'relationships': relationships,
                    'path': path,
                    'path_length': len(path) - 1,
                    'query': f"路径: {source} -> {target}"
                }
            
            # 探索邻居节点
            for neighbor, relation_type in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        # 没有找到路径
        return {
            'success': False,
            'error': f"未找到从 {source} 到 {target} 的路径"
        }
    
    def find_related(self, entity_name):
        """查找与指定实体相关的实体"""
        # 确保实体存在
        if entity_name not in self.graph_data['entities']:
            # 尝试模糊匹配
            matching_entities = []
            for name in self.graph_data['entities']:
                if entity_name.lower() in name.lower():
                    matching_entities.append(name)
                    
            if matching_entities:
                entity_name = matching_entities[0]  # 使用第一个匹配的实体
            else:
                return {
                    'success': False,
                    'error': f"未找到实体: {entity_name}"
                }
        
        nodes = []
        relationships = []
        
        # 添加中心实体
        entity = self.graph_data['entities'][entity_name]
        nodes.append({
            'id': entity_name,
            'label': entity.get('label', 'Entity'),
            'name': entity_name,
            'properties': entity.get('properties', {})
        })
        
        # 记录已添加节点的ID
        added_node_ids = {entity_name}
        
        # 查找相关实体
        for relation in self.graph_data['relations']:
            source = relation.get('source')
            target = relation.get('target')
            
            related_entity_name = None
            if source == entity_name:
                related_entity_name = target
            elif target == entity_name:
                related_entity_name = source
            
            if related_entity_name and related_entity_name in self.graph_data['entities']:
                if related_entity_name not in added_node_ids:
                    related_entity = self.graph_data['entities'][related_entity_name]
                    nodes.append({
                        'id': related_entity_name,
                        'label': related_entity.get('label', 'Entity'),
                        'name': related_entity_name,
                        'properties': related_entity.get('properties', {})
                    })
                    added_node_ids.add(related_entity_name)
                
                # 添加关系
                relationships.append({
                    'source': source,
                    'target': target,
                    'type': relation.get('relation_type', 'RELATED_TO'),
                    'properties': {}
                })
        
        return {
            'success': True,
            'nodes': nodes,
            'relationships': relationships,
            'query': f"与 {entity_name} 相关的实体"
        }

# 创建全局API实例
knowledge_graph_api = KnowledgeGraphAPI()

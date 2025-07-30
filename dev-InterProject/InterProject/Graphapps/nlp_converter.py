import re
from typing import List, Dict

class NLPCypherConverter:
    def __init__(self):
        self.relation_patterns = {
            '包含': [
                r'包含',
                r'包括',
                r'有.*?哪些',
                r'包含.*?什么',
                r'包含.*?哪些'
            ],
            '属于': [
                r'属于',
                r'归类',
                r'分类',
                r'是.*?的.*?一种',
                r'是.*?的.*?类别'
            ],
            '继承': [
                r'继承',
                r'派生',
                r'子类',
                r'父类',
                r'基类'
            ],
            '应用': [
                r'应用',
                r'使用',
                r'用于',
                r'用在',
                r'用途'
            ],
            '属性': [
                r'属性',
                r'特征',
                r'特点',
                r'性质',
                r'特性'
            ]
        }

    def convert(self, query: str) -> str:
        """将自然语言查询转换为Cypher查询"""
        # 提取实体
        entities = self._extract_entities(query)
        
        # 识别关系类型
        relation_type = self._identify_relation_type(query)
        
        # 构建Cypher查询
        if entities and relation_type:
            return self._build_cypher(entities, relation_type)
        elif entities:
            return self._build_entity_query(entities)
        else:
            return self._build_default_query()

    def _extract_entities(self, query: str) -> List[str]:
        """从查询中提取实体"""
        # 移除查询中的动词和关系词
        query = re.sub(r'查找|查询|关于|的', '', query)
        query = query.strip()
        
        # 如果查询中只包含关系类型，返回空列表
        if query in self.relation_patterns:
            return []
            
        return [query]

    def _identify_relation_type(self, query: str) -> str:
        """识别查询中的关系类型"""
        # 直接匹配关系类型
        for rel_type in self.relation_patterns:
            if rel_type in query:
                return rel_type
                
        # 如果直接匹配失败，使用模式匹配
        for rel_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return rel_type
        return None

    def _build_cypher(self, entities: List[str], relation_type: str) -> str:
        """构建Cypher查询"""
        if not entities:  # 如果没有指定实体，查询所有该类型的关系
            return f"""
            MATCH (n:Entity)-[r:{relation_type}]->(m:Entity)
            RETURN n, r, m
            LIMIT 50
            """
        else:
            return f"""
            MATCH (n:Entity)-[r:{relation_type}]->(m:Entity)
            RETURN n, r, m
            LIMIT 50
            """

    def _build_entity_query(self, entities: List[str]) -> str:
        """构建实体查询"""
        if not entities:
            return self._build_default_query()
            
        return f"""
        MATCH (n:Entity)
        WHERE n.name CONTAINS '{entities[0]}'
        RETURN n
        LIMIT 50
        """

    def _build_default_query(self) -> str:
        """构建默认查询"""
        return """
        MATCH (n:Entity)-[r]->(m:Entity)
        RETURN n, r, m
        LIMIT 50
        """ 
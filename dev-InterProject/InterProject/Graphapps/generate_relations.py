#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import pickle
import re
import time
import sys
import random

def load_knowledge_graph():
    """加载知识图谱数据"""
    # 先尝试从pickle文件加载
    if os.path.exists('knowledge_graph.pkl'):
        try:
            with open('knowledge_graph.pkl', 'rb') as f:
                graph_data = pickle.load(f)
                print(f"从pickle文件加载了图谱数据，包含 {len(graph_data.get('entities', {}))} 个实体")
                return graph_data
        except Exception as e:
            print(f"从pickle文件加载失败: {str(e)}")
    
    # 再尝试从JSON文件加载
    if os.path.exists('knowledge_graph.json'):
        try:
            with open('knowledge_graph.json', 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
                print(f"从JSON文件加载了图谱数据，包含 {len(graph_data.get('entities', {}))} 个实体")
                return graph_data
        except Exception as e:
            print(f"从JSON文件加载失败: {str(e)}")
    
    # 最后尝试从collected_knowledge.json加载
    if os.path.exists('data/collected_knowledge.json'):
        try:
            with open('data/collected_knowledge.json', 'r', encoding='utf-8') as f:
                collected_data = json.load(f)
            
            # 处理数据
            graph_data = {
                'entities': {},
                'relations': []
            }
            
            for item in collected_data:
                if item.get('type') == 'entity':
                    graph_data['entities'][item.get('name')] = item
                elif item.get('type') == 'relation':
                    graph_data['relations'].append(item)
            
            print(f"从collected_knowledge.json加载了图谱数据，包含 {len(graph_data.get('entities', {}))} 个实体")
            return graph_data
        except Exception as e:
            print(f"从collected_knowledge.json加载失败: {str(e)}")
    
    print("所有加载尝试都失败，返回空数据")
    return {'entities': {}, 'relations': []}

def generate_prerequisite_relations(graph_data):
    """生成前置关系"""
    relations = []
    
    # 预定义一些知识点前置关系对
    prerequisite_pairs = [
        # 基础计算机科学前置关系
        ("计算机科学", "算法"),
        ("计算机科学", "数据结构"),
        ("计算机科学", "离散数学"),
        ("计算机科学", "计算理论"),
        ("计算机科学", "编程语言"),
        ("计算机科学", "计算机网络"),
        ("计算机科学", "操作系统"),
        ("计算机科学", "数据库"),
        ("计算机科学", "软件工程"),
        ("计算机科学", "计算机组成原理"),
        ("计算理论", "形式语言"),
        ("计算理论", "自动机理论"),
        ("计算理论", "计算复杂性理论"),
        ("离散数学", "图论"),
        ("离散数学", "组合数学"),
        ("离散数学", "逻辑学"),
        ("离散数学", "集合论"),
        ("离散数学", "数论"),
        
        # 数据结构前置关系
        ("数据结构", "算法"),
        ("数据结构", "数组"),
        ("数据结构", "链表"),
        ("数据结构", "栈"),
        ("数据结构", "队列"),
        ("数据结构", "哈希表"),
        ("数据结构", "树"),
        ("数据结构", "图结构"),
        ("树", "二叉树"),
        ("二叉树", "二叉搜索树"),
        ("二叉搜索树", "平衡树"),
        ("平衡树", "AVL树"),
        ("平衡树", "红黑树"),
        ("数据库", "B树"),
        ("数据库", "B+树"),
        ("图结构", "最小生成树"),
        ("图结构", "最短路径"),
        ("图结构", "拓扑排序"),
        
        # 算法前置关系
        ("算法", "排序算法"),
        ("算法", "搜索算法"),
        ("算法", "图算法"),
        ("算法", "动态规划"),
        ("算法", "贪心算法"),
        ("算法", "分治算法"),
        ("算法", "回溯算法"),
        ("算法", "字符串匹配"),
        ("排序算法", "快速排序"),
        ("排序算法", "归并排序"),
        ("排序算法", "堆排序"),
        ("排序算法", "冒泡排序"),
        ("排序算法", "插入排序"),
        ("搜索算法", "二分查找"),
        ("搜索算法", "深度优先搜索"),
        ("搜索算法", "广度优先搜索"),
        ("搜索算法", "A*算法"),
        ("图算法", "最短路径算法"),
        ("图算法", "最小生成树算法"),
        ("字符串匹配", "KMP算法"),
        
        # 编程语言前置关系
        ("编程语言", "Python"),
        ("编程语言", "Java"),
        ("编程语言", "C++"),
        ("编程语言", "JavaScript"),
        ("编程语言", "C语言"),
        ("编程语言", "编程范式"),
        ("编程范式", "面向对象编程"),
        ("编程范式", "函数式编程"),
        ("编程范式", "命令式编程"),
        ("编程范式", "声明式编程"),
        ("编程范式", "逻辑式编程"),
        ("C语言", "C++"),
        ("Java", "Kotlin"),
        ("JavaScript", "TypeScript"),
        ("Python", "数据分析"),
        ("Python", "机器学习"),
        ("Python", "Web开发"),
        
        # 软件工程前置关系
        ("软件工程", "设计模式"),
        ("软件工程", "敏捷开发"),
        ("软件工程", "测试驱动开发"),
        ("软件工程", "持续集成"),
        ("软件工程", "版本控制"),
        ("软件工程", "软件测试"),
        ("软件工程", "需求分析"),
        ("软件工程", "系统设计"),
        ("设计模式", "单例模式"),
        ("设计模式", "工厂模式"),
        ("设计模式", "观察者模式"),
        ("设计模式", "MVC模式"),
        ("敏捷开发", "Scrum"),
        ("敏捷开发", "极限编程"),
        ("敏捷开发", "Kanban"),
        ("软件测试", "单元测试"),
        ("软件测试", "集成测试"),
        ("软件测试", "系统测试"),
        
        # 人工智能前置关系
        ("人工智能", "机器学习"),
        ("人工智能", "深度学习"),
        ("人工智能", "自然语言处理"),
        ("人工智能", "计算机视觉"),
        ("人工智能", "强化学习"),
        ("机器学习", "监督学习"),
        ("机器学习", "无监督学习"),
        ("机器学习", "半监督学习"),
        ("机器学习", "决策树"),
        ("机器学习", "随机森林"),
        ("机器学习", "支持向量机"),
        ("机器学习", "深度学习"),
        ("深度学习", "神经网络"),
        ("深度学习", "卷积神经网络"),
        ("深度学习", "循环神经网络"),
        ("深度学习", "生成对抗网络"),
        ("神经网络", "反向传播"),
        ("神经网络", "梯度下降"),
        ("自然语言处理", "词嵌入"),
        ("自然语言处理", "机器翻译"),
        ("自然语言处理", "情感分析"),
        ("自然语言处理", "命名实体识别"),
        ("计算机视觉", "图像分类"),
        ("计算机视觉", "目标检测"),
        ("计算机视觉", "图像分割"),
        
        # 计算机网络前置关系
        ("计算机网络", "网络协议"),
        ("计算机网络", "网络安全"),
        ("计算机网络", "TCP/IP协议"),
        ("计算机网络", "HTTP协议"),
        ("计算机网络", "OSI七层模型"),
        ("网络协议", "TCP"),
        ("网络协议", "UDP"),
        ("网络协议", "HTTP"),
        ("网络协议", "HTTPS"),
        ("网络协议", "DNS"),
        ("OSI七层模型", "物理层"),
        ("OSI七层模型", "数据链路层"),
        ("OSI七层模型", "网络层"),
        ("OSI七层模型", "传输层"),
        ("OSI七层模型", "会话层"),
        ("OSI七层模型", "表示层"),
        ("OSI七层模型", "应用层"),
        ("网络安全", "加密算法"),
        ("网络安全", "防火墙"),
        ("网络安全", "TLS/SSL"),
        
        # 数据库前置关系
        ("数据库", "关系型数据库"),
        ("数据库", "NoSQL"),
        ("数据库", "SQL语言"),
        ("数据库", "数据库索引"),
        ("数据库", "事务处理"),
        ("关系型数据库", "MySQL"),
        ("关系型数据库", "PostgreSQL"),
        ("关系型数据库", "Oracle"),
        ("关系型数据库", "SQL Server"),
        ("NoSQL", "MongoDB"),
        ("NoSQL", "Redis"),
        ("NoSQL", "Cassandra"),
        ("NoSQL", "Neo4j"),
        ("SQL语言", "查询优化"),
        ("SQL语言", "数据库范式"),
        ("数据库", "数据仓库"),
        ("数据库", "数据湖"),
        
        # 操作系统前置关系
        ("操作系统", "进程管理"),
        ("操作系统", "内存管理"),
        ("操作系统", "文件系统"),
        ("操作系统", "设备管理"),
        ("操作系统", "系统调用"),
        ("进程管理", "进程与线程"),
        ("进程管理", "调度算法"),
        ("进程管理", "同步机制"),
        ("内存管理", "虚拟内存"),
        ("内存管理", "内存分配"),
        ("内存管理", "缓存"),
        ("文件系统", "FAT"),
        ("文件系统", "NTFS"),
        ("文件系统", "ext4"),
        ("操作系统", "Linux"),
        ("操作系统", "Windows"),
        ("操作系统", "macOS"),
        
        # 前端与移动开发前置关系
        ("Web开发", "前端开发"),
        ("Web开发", "后端开发"),
        ("前端开发", "HTML"),
        ("前端开发", "CSS"),
        ("前端开发", "JavaScript"),
        ("前端开发", "React"),
        ("前端开发", "Vue.js"),
        ("前端开发", "Angular"),
        ("后端开发", "Node.js"),
        ("后端开发", "Spring框架"),
        ("后端开发", "Django"),
        ("移动应用开发", "Android开发"),
        ("移动应用开发", "iOS开发"),
        ("移动应用开发", "Flutter"),
        ("Android开发", "Kotlin"),
        ("iOS开发", "Swift"),
    ]
    
    # 检查每对前置关系中的实体是否存在，如果存在就添加关系
    for prereq, subject in prerequisite_pairs:
        # 模糊匹配
        prereq_entity = None
        subject_entity = None
        
        # 尝试精确匹配
        if prereq in graph_data['entities']:
            prereq_entity = graph_data['entities'][prereq]
        if subject in graph_data['entities']:
            subject_entity = graph_data['entities'][subject]
        
        # 如果精确匹配失败，尝试模糊匹配
        if not prereq_entity:
            for name, entity in graph_data['entities'].items():
                if prereq.lower() in name.lower():
                    prereq_entity = entity
                    prereq = name
                    break
        
        if not subject_entity:
            for name, entity in graph_data['entities'].items():
                if subject.lower() in name.lower():
                    subject_entity = entity
                    subject = name
                    break
        
        # 如果两个实体都找到了，就添加前置关系
        if prereq_entity and subject_entity and prereq != subject:
            # 检查关系是否已存在
            relation_exists = False
            for relation in graph_data['relations']:
                if (relation.get('source') == prereq and 
                    relation.get('target') == subject and 
                    relation.get('relation_type') == 'PREREQUISITE'):
                    relation_exists = True
                    break
            
            if not relation_exists:
                relation = {
                    'type': 'relation',
                    'source': prereq,
                    'target': subject,
                    'relation_type': 'PREREQUISITE',
                    'source_type': 'generated',
                    'confidence': 0.8,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                relations.append(relation)
    
    print(f"生成了 {len(relations)} 个前置关系")
    return relations

def generate_related_relations(graph_data):
    """生成相关关系"""
    relations = []
    
    # 预定义一些相关知识点对
    related_pairs = [
        # 基础计算机科学相关关系
        ("算法", "数据结构"),
        ("算法", "计算理论"),
        ("算法", "计算复杂性理论"),
        ("数据结构", "离散数学"),
        ("数据结构", "图论"),
        ("离散数学", "计算理论"),
        ("计算理论", "形式语言"),
        ("形式语言", "自动机理论"),
        ("离散数学", "密码学"),
        
        # 算法和数据结构相关关系
        ("排序算法", "数组"),
        ("搜索算法", "数组"),
        ("搜索算法", "树"),
        ("图算法", "图结构"),
        ("动态规划", "分治算法"),
        ("贪心算法", "最优化"),
        ("最短路径算法", "图结构"),
        ("最小生成树算法", "图结构"),
        ("哈希表", "散列函数"),
        ("树", "递归"),
        ("二叉树", "树遍历"),
        ("红黑树", "平衡树"),
        ("快速排序", "分治算法"),
        ("堆排序", "堆"),
        ("深度优先搜索", "栈"),
        ("广度优先搜索", "队列"),
        
        # 编程语言相关关系
        ("Java", "面向对象编程"),
        ("C++", "面向对象编程"),
        ("Python", "脚本语言"),
        ("JavaScript", "Web开发"),
        ("TypeScript", "JavaScript"),
        ("函数式编程", "Lambda表达式"),
        ("面向对象编程", "封装"),
        ("面向对象编程", "继承"),
        ("面向对象编程", "多态"),
        ("静态类型", "编译时检查"),
        ("动态类型", "运行时检查"),
        ("Python", "数据分析"),
        ("R语言", "数据分析"),
        ("Shell脚本", "自动化"),
        ("Ruby", "Web开发"),
        
        # 软件工程相关关系
        ("敏捷开发", "持续集成"),
        ("持续集成", "自动化测试"),
        ("设计模式", "软件设计"),
        ("软件测试", "质量保证"),
        ("版本控制", "Git"),
        ("版本控制", "SVN"),
        ("单元测试", "测试驱动开发"),
        ("重构", "技术债务"),
        ("需求分析", "用户故事"),
        ("Scrum", "敏捷开发"),
        ("DevOps", "持续部署"),
        ("持续集成", "持续部署"),
        ("代码审查", "质量保证"),
        ("软件架构", "系统设计"),
        
        # 人工智能相关关系
        ("机器学习", "数据挖掘"),
        ("机器学习", "人工智能"),
        ("深度学习", "人工智能"),
        ("自然语言处理", "机器学习"),
        ("计算机视觉", "机器学习"),
        ("神经网络", "深度学习"),
        ("卷积神经网络", "图像处理"),
        ("循环神经网络", "序列数据"),
        ("生成对抗网络", "图像生成"),
        ("监督学习", "分类"),
        ("监督学习", "回归"),
        ("无监督学习", "聚类"),
        ("强化学习", "决策过程"),
        ("自然语言处理", "语言模型"),
        ("计算机视觉", "图像识别"),
        ("Transformer", "注意力机制"),
        ("BERT", "语言理解"),
        ("GPT", "语言生成"),
        
        # 网络与系统相关关系
        ("计算机网络", "分布式系统"),
        ("计算机网络", "网络安全"),
        ("TCP/IP协议", "互联网"),
        ("HTTP协议", "Web开发"),
        ("DNS", "域名解析"),
        ("操作系统", "计算机体系结构"),
        ("文件系统", "存储管理"),
        ("内存管理", "虚拟内存"),
        ("进程管理", "调度算法"),
        ("网络安全", "加密技术"),
        ("加密算法", "密码学"),
        ("Linux", "开源软件"),
        ("系统调用", "API"),
        ("计算机体系结构", "CPU设计"),
        ("并发编程", "多线程"),
        
        # 数据库相关关系
        ("数据库", "数据管理"),
        ("关系型数据库", "SQL"),
        ("NoSQL", "大数据"),
        ("MySQL", "Web应用"),
        ("PostgreSQL", "企业应用"),
        ("MongoDB", "文档存储"),
        ("Redis", "缓存"),
        ("数据库索引", "查询优化"),
        ("数据库事务", "ACID"),
        ("数据仓库", "商业智能"),
        ("数据湖", "大数据处理"),
        ("图数据库", "图算法"),
        ("分布式数据库", "高可用性"),
        ("ORM", "对象关系映射"),
        ("ETL", "数据集成"),
        
        # 前端与移动开发相关关系
        ("前端开发", "用户界面"),
        ("HTML", "Web标准"),
        ("CSS", "Web设计"),
        ("JavaScript", "交互设计"),
        ("React", "组件化"),
        ("Vue.js", "响应式设计"),
        ("Angular", "TypeScript"),
        ("Web开发", "响应式设计"),
        ("移动应用开发", "跨平台开发"),
        ("Android开发", "Java"),
        ("iOS开发", "Swift"),
        ("Flutter", "跨平台开发"),
        ("前端框架", "单页应用"),
        ("WebSocket", "实时通信"),
        ("RESTful API", "后端交互"),
        
        # 云计算与新兴技术相关关系
        ("云计算", "虚拟化技术"),
        ("分布式系统", "可扩展性"),
        ("容器技术", "Docker"),
        ("Docker", "Kubernetes"),
        ("微服务", "服务治理"),
        ("区块链", "去中心化"),
        ("物联网", "嵌入式系统"),
        ("5G技术", "移动通信"),
        ("边缘计算", "实时处理"),
        ("大数据", "数据处理"),
        ("Hadoop", "分布式文件系统"),
        ("Spark", "内存计算"),
        ("量子计算", "量子算法"),
        ("虚拟现实", "3D建模"),
        ("增强现实", "计算机视觉")
    ]
    
    # 检查每对相关关系中的实体是否存在，如果存在就添加关系
    for entity1, entity2 in related_pairs:
        # 模糊匹配
        entity1_obj = None
        entity2_obj = None
        
        # 尝试精确匹配
        if entity1 in graph_data['entities']:
            entity1_obj = graph_data['entities'][entity1]
        if entity2 in graph_data['entities']:
            entity2_obj = graph_data['entities'][entity2]
        
        # 如果精确匹配失败，尝试模糊匹配
        if not entity1_obj:
            for name, entity in graph_data['entities'].items():
                if entity1.lower() in name.lower():
                    entity1_obj = entity
                    entity1 = name
                    break
        
        if not entity2_obj:
            for name, entity in graph_data['entities'].items():
                if entity2.lower() in name.lower():
                    entity2_obj = entity
                    entity2 = name
                    break
        
        # 如果两个实体都找到了，就添加相关关系
        if entity1_obj and entity2_obj and entity1 != entity2:
            # 检查关系是否已存在
            relation_exists = False
            for relation in graph_data['relations']:
                if ((relation.get('source') == entity1 and relation.get('target') == entity2) or
                    (relation.get('source') == entity2 and relation.get('target') == entity1)) and \
                    relation.get('relation_type') == 'RELATED_TO':
                    relation_exists = True
                    break
            
            if not relation_exists:
                relation = {
                    'type': 'relation',
                    'source': entity1,
                    'target': entity2,
                    'relation_type': 'RELATED_TO',
                    'source_type': 'generated',
                    'confidence': 0.8,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                relations.append(relation)
    
    print(f"生成了 {len(relations)} 个相关关系")
    return relations

def generate_parent_child_relations(graph_data):
    """生成父子关系"""
    relations = []
    
    # 预定义一些父子关系对
    parent_child_pairs = [
        ("算法", "排序算法"),
        ("算法", "搜索算法"),
        ("算法", "图算法"),
        ("算法", "动态规划"),
        ("数据结构", "数组"),
        ("数据结构", "链表"),
        ("数据结构", "树"),
        ("数据结构", "图"),
        ("数据结构", "栈"),
        ("数据结构", "队列"),
        ("数据结构", "哈希表"),
        ("编程语言", "Python"),
        ("编程语言", "Java"),
        ("编程语言", "C++"),
        ("编程语言", "JavaScript"),
        ("编程语言", "Go"),
        ("人工智能", "机器学习"),
        ("人工智能", "深度学习"),
        ("人工智能", "自然语言处理"),
        ("人工智能", "计算机视觉"),
        ("机器学习", "监督学习"),
        ("机器学习", "无监督学习"),
        ("机器学习", "强化学习"),
        ("深度学习", "神经网络"),
        ("深度学习", "卷积神经网络"),
        ("深度学习", "循环神经网络"),
        ("深度学习", "生成对抗网络"),
        ("计算机科学", "操作系统"),
        ("计算机科学", "计算机网络"),
        ("计算机科学", "数据库"),
        ("计算机科学", "编译原理"),
        ("计算机科学", "软件工程"),
        ("软件工程", "软件设计"),
        ("软件工程", "软件测试"),
        ("软件工程", "软件维护"),
        ("软件工程", "DevOps"),
        ("计算机网络", "网络协议"),
        ("计算机网络", "网络安全"),
        ("计算机网络", "网络架构"),
        ("数据库", "关系型数据库"),
        ("数据库", "非关系型数据库"),
        ("数据库", "数据仓库"),
        ("关系型数据库", "MySQL"),
        ("关系型数据库", "PostgreSQL"),
        ("关系型数据库", "Oracle"),
        ("非关系型数据库", "MongoDB"),
        ("非关系型数据库", "Redis"),
        ("非关系型数据库", "Cassandra")
    ]
    
    # 检查每对父子关系中的实体是否存在，如果存在就添加关系
    for parent, child in parent_child_pairs:
        # 模糊匹配
        parent_entity = None
        child_entity = None
        
        # 尝试精确匹配
        if parent in graph_data['entities']:
            parent_entity = graph_data['entities'][parent]
        if child in graph_data['entities']:
            child_entity = graph_data['entities'][child]
        
        # 如果精确匹配失败，尝试模糊匹配
        if not parent_entity:
            for name, entity in graph_data['entities'].items():
                if parent.lower() in name.lower():
                    parent_entity = entity
                    parent = name
                    break
        
        if not child_entity:
            for name, entity in graph_data['entities'].items():
                if child.lower() in name.lower():
                    child_entity = entity
                    child = name
                    break
        
        # 如果两个实体都找到了，就添加父子关系
        if parent_entity and child_entity and parent != child:
            # 检查关系是否已存在
            relation_exists = False
            for relation in graph_data['relations']:
                if (relation.get('source') == parent and 
                    relation.get('target') == child and 
                    relation.get('relation_type') == 'CONTAINS'):
                    relation_exists = True
                    break
            
            if not relation_exists:
                relation = {
                    'type': 'relation',
                    'source': parent,
                    'target': child,
                    'relation_type': 'CONTAINS',
                    'source_type': 'generated',
                    'confidence': 0.85,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                relations.append(relation)
    
    print(f"生成了 {len(relations)} 个父子关系")
    return relations

def generate_relations_based_on_text(graph_data):
    """基于文本内容生成关系"""
    relations = []
    
    # 获取所有实体的名称和描述
    entities = list(graph_data['entities'].values())
    
    # 对于每个实体，检查其描述中是否包含其他实体的名称
    for entity in entities:
        entity_name = entity.get('name', '')
        entity_desc = entity.get('properties', {}).get('description', '')
        
        if not entity_name or not entity_desc:
            continue
        
        # 检查描述中是否包含其他实体的名称
        for other_entity in entities:
            other_name = other_entity.get('name', '')
            
            # 跳过自身和名称为空的实体
            if not other_name or entity_name == other_name:
                continue
            
            # 如果描述中包含其他实体的名称，添加关系
            if re.search(r'\b' + re.escape(other_name) + r'\b', entity_desc, re.IGNORECASE):
                # 检查关系是否已存在
                relation_exists = False
                for relation in graph_data['relations']:
                    if (relation.get('source') == entity_name and 
                        relation.get('target') == other_name):
                        relation_exists = True
                        break
                
                if not relation_exists:
                    relation = {
                        'type': 'relation',
                        'source': entity_name,
                        'target': other_name,
                        'relation_type': 'RELATED_TO',
                        'source_type': 'text_based',
                        'confidence': 0.7,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    relations.append(relation)
    
    print(f"基于文本内容生成了 {len(relations)} 个关系")
    return relations

def generate_course_knowledge_relations(graph_data):
    """生成课程-知识点关系"""
    relations = []
    
    # 首先从图谱数据中提取课程和知识点
    courses = {}
    knowledge_points = {}
    
    for name, entity in graph_data['entities'].items():
        if entity.get('label') == 'Course':
            courses[name] = entity
        elif entity.get('label') == 'KnowledgePoint':
            knowledge_points[name] = entity
    
    print(f"找到 {len(courses)} 个课程和 {len(knowledge_points)} 个知识点")
    
    # 如果课程数量太少，自动创建一些新课程
    if len(courses) < 10:
        new_courses = generate_computer_science_courses(knowledge_points)
        for course_name, course in new_courses.items():
            if course_name not in courses:
                graph_data['entities'][course_name] = course
                courses[course_name] = course
        
        print(f"创建了 {len(new_courses)} 个新课程，现在共有 {len(courses)} 个课程")
    
    # 预定义一些课程-知识点关系
    course_knowledge_pairs = [
        # 数据结构与算法课程
        ("数据结构与算法", ["数据结构", "算法", "排序算法", "搜索算法", "图算法", "动态规划", 
                    "数组", "链表", "栈", "队列", "哈希表", "树", "图结构", "二叉树"]),
        
        # 操作系统课程
        ("操作系统", ["操作系统", "进程与线程", "内存管理", "文件系统", "设备管理", "系统调用", 
                  "调度算法", "死锁", "同步机制", "虚拟内存"]),
        
        # 计算机网络课程
        ("计算机网络", ["计算机网络", "网络协议", "TCP/IP协议", "HTTP协议", "网络安全", 
                   "OSI七层模型", "IP地址", "路由算法", "DNS", "网络编程"]),
        
        # 数据库系统课程
        ("数据库系统", ["数据库", "关系型数据库", "SQL语言", "数据库索引", "事务处理", 
                   "数据库设计", "查询优化", "数据库安全", "MySQL", "PostgreSQL"]),
        
        # 编译原理课程
        ("编译原理", ["编译原理", "词法分析", "语法分析", "语义分析", "中间代码生成", 
                 "代码优化", "目标代码生成", "形式语言", "自动机理论"]),
        
        # 软件工程课程
        ("软件工程", ["软件工程", "软件生命周期", "需求分析", "系统设计", "软件测试", 
                 "项目管理", "设计模式", "版本控制", "敏捷开发", "质量保证"]),
        
        # 计算机组成原理课程
        ("计算机组成原理", ["计算机组成原理", "CPU设计", "指令集", "存储系统", "输入输出系统", 
                     "总线", "中断", "RISC", "CISC", "流水线"]),
        
        # 人工智能课程
        ("人工智能", ["人工智能", "机器学习", "深度学习", "自然语言处理", "计算机视觉", 
                 "知识表示", "推理系统", "搜索算法", "规划", "专家系统"]),
        
        # 机器学习课程
        ("机器学习", ["机器学习", "监督学习", "无监督学习", "强化学习", "神经网络", 
                 "决策树", "支持向量机", "朴素贝叶斯", "聚类算法", "降维"]),
        
        # 深度学习课程
        ("深度学习", ["深度学习", "神经网络", "卷积神经网络", "循环神经网络", "生成对抗网络", 
                 "注意力机制", "Transformer", "迁移学习", "强化学习"]),
        
        # Web开发课程
        ("Web开发", ["Web开发", "HTML", "CSS", "JavaScript", "前端开发", "后端开发", 
                 "数据库", "HTTP协议", "RESTful API", "Web框架"]),
        
        # 移动应用开发课程
        ("移动应用开发", ["移动应用开发", "Android开发", "iOS开发", "跨平台开发", "Flutter", 
                    "React Native", "UI设计", "移动数据库", "移动网络"]),
        
        # 网络安全课程
        ("网络安全", ["网络安全", "加密算法", "网络攻击", "防火墙", "入侵检测", 
                 "安全协议", "认证", "授权", "漏洞分析", "安全编程"]),
        
        # 云计算课程
        ("云计算", ["云计算", "虚拟化", "容器技术", "分布式系统", "云存储", 
                "云数据库", "负载均衡", "高可用性", "可扩展性", "云安全"]),
        
        # 大数据课程
        ("大数据", ["大数据", "数据挖掘", "数据仓库", "数据湖", "Hadoop", 
                "Spark", "流处理", "批处理", "数据可视化", "商业智能"])
    ]
    
    # 为每对课程-知识点关系创建关系
    for course_name, knowledge_list in course_knowledge_pairs:
        # 找到课程实体，如果不存在则创建一个
        course_entity = None
        
        # 精确匹配
        if course_name in courses:
            course_entity = courses[course_name]
        else:
            # 模糊匹配
            for name, entity in courses.items():
                if course_name.lower() in name.lower() or name.lower() in course_name.lower():
                    course_entity = entity
                    course_name = name  # 使用已有的课程名
                    break
        
        # 如果没有找到匹配的课程，创建一个新课程
        if not course_entity:
            course_entity = {
                'type': 'entity',
                'name': course_name,
                'label': 'Course',
                'source': 'generated',
                'confidence': 0.8,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'properties': {
                    'description': f"{course_name}是计算机科学的重要课程，涵盖{', '.join(knowledge_list[:3])}等知识点",
                    'instructor': '系统生成',
                    'url': f"https://example.com/course/{course_name.replace(' ', '-')}",
                    'topics': knowledge_list[:5]  # 使用前5个知识点作为主题
                }
            }
            graph_data['entities'][course_name] = course_entity
            courses[course_name] = course_entity
            print(f"创建了新课程: {course_name}")
        
        # 为每个知识点创建与课程的关系
        for knowledge_name in knowledge_list:
            # 找到知识点实体，如果不存在则创建一个
            knowledge_entity = None
            
            # 精确匹配
            if knowledge_name in knowledge_points:
                knowledge_entity = knowledge_points[knowledge_name]
            else:
                # 模糊匹配
                for name, entity in knowledge_points.items():
                    if knowledge_name.lower() in name.lower() or name.lower() in knowledge_name.lower():
                        knowledge_entity = entity
                        knowledge_name = name  # 使用已有的知识点名
                        break
            
            # 如果没有找到匹配的知识点，创建一个新知识点
            if not knowledge_entity:
                knowledge_entity = {
                    'type': 'entity',
                    'name': knowledge_name,
                    'label': 'KnowledgePoint',
                    'source': 'generated',
                    'confidence': 0.8,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'properties': {
                        'description': f"{knowledge_name}是计算机科学中的重要概念或技术",
                        'category': '计算机科学',
                        'url': f"https://example.com/topic/{knowledge_name.replace(' ', '-')}",
                        'related_topics': []  # 后续会通过相关关系生成
                    }
                }
                graph_data['entities'][knowledge_name] = knowledge_entity
                knowledge_points[knowledge_name] = knowledge_entity
                print(f"创建了新知识点: {knowledge_name}")
            
            # 创建课程-知识点关系
            relation_exists = False
            for relation in graph_data['relations']:
                if (relation.get('source') == course_name and 
                    relation.get('target') == knowledge_name and 
                    relation.get('relation_type') == 'CONTAINS'):
                    relation_exists = True
                    break
            
            if not relation_exists:
                relation = {
                    'type': 'relation',
                    'source': course_name,
                    'target': knowledge_name,
                    'relation_type': 'CONTAINS',
                    'source_type': 'generated',
                    'confidence': 0.9,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                relations.append(relation)
    
    print(f"生成了 {len(relations)} 个课程-知识点关系")
    return relations

def generate_computer_science_courses(knowledge_points):
    """生成计算机科学课程"""
    courses = {}
    
    # 预定义一些计算机科学课程及其描述
    course_templates = [
        {
            "name": "数据结构与算法",
            "description": "介绍基本的数据结构和算法设计与分析，包括数组、链表、栈、队列、树、图等数据结构和排序、搜索、动态规划等算法",
            "keywords": ["数据结构", "算法", "排序算法", "搜索算法", "数组", "链表", "树", "图结构"]
        },
        {
            "name": "计算机组成原理",
            "description": "讲解计算机硬件系统的基本组成、工作原理和设计方法，包括CPU、存储系统、I/O设备等",
            "keywords": ["计算机组成原理", "CPU设计", "存储系统", "总线", "指令集", "流水线"]
        },
        {
            "name": "操作系统",
            "description": "研究操作系统的基本概念、原理和实现方法，包括进程管理、内存管理、文件系统等",
            "keywords": ["操作系统", "进程与线程", "内存管理", "文件系统", "调度算法", "死锁"]
        },
        {
            "name": "计算机网络",
            "description": "探讨计算机网络的基本原理、协议和应用，包括网络架构、TCP/IP协议族、互联网应用等",
            "keywords": ["计算机网络", "网络协议", "TCP/IP协议", "HTTP协议", "OSI七层模型", "路由算法"]
        },
        {
            "name": "数据库系统",
            "description": "学习数据库系统的设计、实现和管理，包括关系模型、SQL语言、事务处理、并发控制等",
            "keywords": ["数据库", "关系型数据库", "SQL语言", "事务处理", "数据库索引", "查询优化"]
        },
        {
            "name": "软件工程",
            "description": "研究软件开发的工程化方法，包括需求分析、系统设计、测试验证和项目管理等",
            "keywords": ["软件工程", "需求分析", "系统设计", "软件测试", "项目管理", "设计模式"]
        },
        {
            "name": "编译原理",
            "description": "探讨程序语言的编译过程，包括词法分析、语法分析、语义分析和代码生成等",
            "keywords": ["编译原理", "词法分析", "语法分析", "语义分析", "中间代码生成", "代码优化"]
        },
        {
            "name": "人工智能导论",
            "description": "介绍人工智能的基本概念、方法和应用，包括搜索策略、知识表示、机器学习等",
            "keywords": ["人工智能", "机器学习", "知识表示", "搜索算法", "推理系统", "专家系统"]
        },
        {
            "name": "机器学习",
            "description": "研究计算机系统如何通过经验自动改进性能，包括监督学习、无监督学习和强化学习等",
            "keywords": ["机器学习", "监督学习", "无监督学习", "强化学习", "神经网络", "决策树"]
        },
        {
            "name": "深度学习",
            "description": "探讨基于深层神经网络的学习方法，包括卷积神经网络、循环神经网络和生成对抗网络等",
            "keywords": ["深度学习", "神经网络", "卷积神经网络", "循环神经网络", "生成对抗网络", "注意力机制"]
        },
        {
            "name": "计算机图形学",
            "description": "学习计算机生成和处理图像的原理和技术，包括3D建模、渲染、动画和可视化等",
            "keywords": ["计算机图形学", "3D建模", "渲染", "光线追踪", "动画", "图像处理"]
        },
        {
            "name": "Web开发",
            "description": "介绍Web应用程序的开发技术，包括前端技术、后端框架、数据库集成和Web服务等",
            "keywords": ["Web开发", "HTML", "CSS", "JavaScript", "前端开发", "后端开发"]
        },
        {
            "name": "移动应用开发",
            "description": "学习在移动平台上开发应用程序的方法和技术，包括Android和iOS应用开发",
            "keywords": ["移动应用开发", "Android开发", "iOS开发", "Flutter", "React Native", "UI设计"]
        },
        {
            "name": "网络安全",
            "description": "研究保护计算机系统和网络安全的方法和技术，包括密码学、网络安全协议和安全编程等",
            "keywords": ["网络安全", "加密算法", "防火墙", "安全协议", "漏洞分析", "入侵检测"]
        },
        {
            "name": "云计算",
            "description": "探讨云计算的基本概念、架构和关键技术，包括虚拟化、容器技术和分布式系统等",
            "keywords": ["云计算", "虚拟化", "容器技术", "分布式系统", "云存储", "负载均衡"]
        },
        {
            "name": "大数据技术",
            "description": "学习处理和分析大规模数据的方法和技术，包括分布式存储、并行计算和数据挖掘等",
            "keywords": ["大数据", "数据挖掘", "Hadoop", "Spark", "数据仓库", "数据可视化"]
        },
        {
            "name": "区块链技术",
            "description": "介绍区块链的基本原理、架构和应用，包括共识算法、智能合约和加密货币等",
            "keywords": ["区块链", "加密货币", "智能合约", "共识算法", "分布式账本", "去中心化"]
        },
        {
            "name": "物联网技术",
            "description": "研究将物理设备连接到互联网的技术和应用，包括嵌入式系统、传感器网络和数据分析等",
            "keywords": ["物联网", "嵌入式系统", "传感器网络", "MQTT", "实时数据", "边缘计算"]
        },
        {
            "name": "自然语言处理",
            "description": "探讨计算机处理和理解人类语言的方法和技术，包括文本分析、机器翻译和对话系统等",
            "keywords": ["自然语言处理", "语言模型", "文本分类", "情感分析", "机器翻译", "对话系统"]
        },
        {
            "name": "计算机视觉",
            "description": "学习计算机理解和分析图像和视频的方法和技术，包括图像识别、目标检测和视频分析等",
            "keywords": ["计算机视觉", "图像识别", "目标检测", "图像分割", "人脸识别", "视频分析"]
        }
    ]
    
    # 为每个课程模板创建课程实体
    for template in course_templates:
        course_name = template["name"]
        course = {
            'type': 'entity',
            'name': course_name,
            'label': 'Course',
            'source': 'generated',
            'confidence': 0.9,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'properties': {
                'description': template["description"],
                'instructor': '系统生成',
                'url': f"https://example.com/course/{course_name.replace(' ', '-')}",
                'topics': template["keywords"]
            }
        }
        courses[course_name] = course
    
    print(f"生成了 {len(courses)} 个计算机科学课程")
    return courses

def save_graph_data(graph_data):
    """保存图谱数据到文件"""
    try:
        # 保存为pickle文件
        with open('knowledge_graph.pkl', 'wb') as f:
            pickle.dump(graph_data, f)
        
        # 保存为JSON文件
        with open('knowledge_graph.json', 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        
        print(f"图谱数据保存成功，包含 {len(graph_data.get('entities', {}))} 个实体和 {len(graph_data.get('relations', []))} 个关系")
        return True
    except Exception as e:
        print(f"保存图谱数据失败: {str(e)}")
        return False

def generate_course_course_relations(graph_data):
    """生成课程与课程之间的关系"""
    relations = []
    
    # 首先从图谱数据中提取所有课程实体
    courses = {}
    for name, entity in graph_data['entities'].items():
        if entity.get('label') == 'Course':
            courses[name] = entity
    
    print(f"为 {len(courses)} 个课程生成课程间关系")
    
    # 预定义一些课程之间的层次关系（课程A是课程B的先导课程）
    course_prerequisite_pairs = [
        # 基础课程为高级课程的先修课
        ("计算机科学概论", ["数据结构与算法", "计算机网络", "操作系统", "数据库系统"]),
        ("数据结构与算法", ["算法设计与分析", "高级算法", "人工智能", "机器学习"]),
        ("计算机组成原理", ["操作系统", "计算机体系结构", "编译原理"]),
        ("操作系统", ["分布式系统", "云计算", "高性能计算"]),
        ("计算机网络", ["网络安全", "云计算", "物联网"]),
        ("数据库系统", ["数据挖掘", "大数据", "数据仓库"]),
        ("离散数学", ["算法设计与分析", "编译原理", "密码学"]),
        ("软件工程", ["软件测试", "软件架构", "DevOps"]),
        ("编程基础", ["Web开发", "移动应用开发", "游戏开发"]),
        ("机器学习", ["深度学习", "自然语言处理", "计算机视觉"]),
    ]
    
    # 为每对先修关系创建关系实体
    for prerequisite, advanced_courses in course_prerequisite_pairs:
        # 检查先修课程是否存在
        prerequisite_entity = None
        for course_name in courses.keys():
            if prerequisite.lower() in course_name.lower() or course_name.lower() in prerequisite.lower():
                prerequisite_entity = course_name
                break
        
        if not prerequisite_entity:
            continue  # 如果先修课程不存在，则跳过
        
        # 为每个高级课程创建关系
        for advanced_course in advanced_courses:
            # 检查高级课程是否存在
            advanced_entity = None
            for course_name in courses.keys():
                if advanced_course.lower() in course_name.lower() or course_name.lower() in advanced_course.lower():
                    advanced_entity = course_name
                    break
            
            if not advanced_entity:
                continue  # 如果高级课程不存在，则跳过
            
            # 创建先修关系
            relation = {
                'type': 'relation',
                'source': prerequisite_entity,
                'target': advanced_entity,
                'relation_type': 'PREREQUISITE',
                'source_type': 'generated',
                'confidence': 0.85,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            relations.append(relation)
    
    # 创建课程相关关系 - 基于共同的知识点
    # 首先构建课程-知识点的映射
    course_to_knowledge = {}
    for relation in graph_data['relations']:
        if relation.get('relation_type') == 'CONTAINS':
            course = relation.get('source')
            knowledge = relation.get('target')
            
            if course in courses and knowledge:
                if course not in course_to_knowledge:
                    course_to_knowledge[course] = []
                course_to_knowledge[course].append(knowledge)
    
    # 根据共同知识点生成课程间的相关关系
    course_names = list(courses.keys())
    for i, course1 in enumerate(course_names):
        for course2 in course_names[i+1:]:
            # 跳过已经有先修关系的课程对
            has_prerequisite = False
            for relation in relations:
                if (relation.get('source') == course1 and relation.get('target') == course2) or \
                   (relation.get('source') == course2 and relation.get('target') == course1):
                    has_prerequisite = True
                    break
            
            if has_prerequisite:
                continue
            
            # 检查共同知识点
            knowledge_set1 = set(course_to_knowledge.get(course1, []))
            knowledge_set2 = set(course_to_knowledge.get(course2, []))
            common_knowledge = knowledge_set1.intersection(knowledge_set2)
            
            # 如果有足够数量的共同知识点，则创建相关关系
            if len(common_knowledge) >= 2:
                relation = {
                    'type': 'relation',
                    'source': course1,
                    'target': course2,
                    'relation_type': 'RELATED_TO',
                    'source_type': 'generated',
                    'confidence': 0.75,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                relations.append(relation)
    
    print(f"生成了 {len(relations)} 个课程间关系")
    return relations

def main():
    """主函数"""
    print("开始生成实体关系...")
    
    # 1. 加载知识图谱数据
    graph_data = load_knowledge_graph()
    
    # 记录原始关系数量
    original_relations_count = len(graph_data.get('relations', []))
    print(f"原始图谱包含 {len(graph_data.get('entities', {}))} 个实体和 {original_relations_count} 个关系")
    
    # 2. 生成前置关系
    prereq_relations = generate_prerequisite_relations(graph_data)
    graph_data['relations'].extend(prereq_relations)
    
    # 3. 生成相关关系
    related_relations = generate_related_relations(graph_data)
    graph_data['relations'].extend(related_relations)
    
    # 4. 生成父子关系
    parent_child_relations = generate_parent_child_relations(graph_data)
    graph_data['relations'].extend(parent_child_relations)
    
    # 5. 基于文本内容生成关系
    text_based_relations = generate_relations_based_on_text(graph_data)
    graph_data['relations'].extend(text_based_relations)
    
    # 6. 生成课程-知识点关系
    course_kp_relations = generate_course_knowledge_relations(graph_data)
    graph_data['relations'].extend(course_kp_relations)
    
    # 7. 生成课程-课程关系
    course_relations = generate_course_course_relations(graph_data)
    graph_data['relations'].extend(course_relations)
    
    # 保存更新后的图谱数据
    save_graph_data(graph_data)
    
    # 计算添加的关系数量
    new_relations_count = len(graph_data.get('relations', []))
    added_relations_count = new_relations_count - original_relations_count
    
    print(f"共添加了 {added_relations_count} 个新关系")
    print(f"最终图谱包含 {len(graph_data.get('entities', {}))} 个实体和 {new_relations_count} 个关系")

if __name__ == "__main__":
    main() 
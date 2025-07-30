#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import pickle
import sys
import time

# 定义核心知识点列表，确保这些关键实体始终存在于知识图谱中
CORE_KNOWLEDGE_POINTS = [
    '算法', '数据结构', '人工智能', '机器学习', '深度学习',
    '计算机网络', '操作系统', '数据库', '软件工程', '编译原理'
]


def merge_entities_and_resolve_conflicts(data_list):
    """合并多个数据源的实体和关系，并解决冲突"""
    merged_data = {
        'entities': {},
        'relations': []
    }

    # 跟踪实体名称映射（处理重名情况）
    name_mapping = {}
    total_entities = 0
    total_relations = 0

    # 处理每个数据源
    for data_source in data_list:
        if isinstance(data_source, dict):
            # 处理实体
            entities = data_source.get('entities', {})
            if isinstance(entities, dict):
                for name, entity in entities.items():
                    if name in merged_data['entities']:
                        # 实体已存在，合并属性
                        existing_entity = merged_data['entities'][name]
                        if 'properties' in entity and 'properties' in existing_entity:
                            # 合并属性，保留更高置信度的属性
                            if entity.get('confidence', 0) > existing_entity.get('confidence', 0):
                                for key, value in entity['properties'].items():
                                    existing_entity['properties'][key] = value
                                existing_entity['confidence'] = entity.get('confidence', 0)
                        # 记录映射
                        name_mapping[name] = name
                    else:
                        # 新实体
                        merged_data['entities'][name] = entity
                        name_mapping[name] = name
                        total_entities += 1

            # 处理关系
            relations = data_source.get('relations', [])
            if isinstance(relations, list):
                for relation in relations:
                    # 获取源和目标
                    source = relation.get('source')
                    target = relation.get('target')

                    # 检查源和目标是否存在
                    if source in name_mapping and target in name_mapping:
                        # 映射到规范化的名称
                        mapped_source = name_mapping[source]
                        mapped_target = name_mapping[target]

                        # 创建关系的标识符
                        relation_id = f"{mapped_source}_{relation.get('relation_type')}_{mapped_target}"

                        # 检查关系是否已存在
                        relation_exists = False
                        for existing_relation in merged_data['relations']:
                            existing_source = existing_relation.get('source')
                            existing_target = existing_relation.get('target')
                            existing_type = existing_relation.get('relation_type')

                            if (existing_source == mapped_source and
                                    existing_target == mapped_target and
                                    existing_type == relation.get('relation_type')):
                                relation_exists = True
                                # 如果新关系的置信度更高，更新置信度
                                if relation.get('confidence', 0) > existing_relation.get('confidence', 0):
                                    existing_relation['confidence'] = relation.get('confidence', 0)
                                break

                        # 如果关系不存在，添加它，但使用映射后的名称
                        if not relation_exists:
                            new_relation = relation.copy()
                            new_relation['source'] = mapped_source
                            new_relation['target'] = mapped_target
                            merged_data['relations'].append(new_relation)
                            total_relations += 1

    print(f"合并完成，总共 {total_entities} 个实体和 {total_relations} 个关系")
    return merged_data


def process_large_dataset(data):
    """处理大规模数据集，提高效率"""
    print("开始处理大规模数据集...")

    # 使用集合去重
    unique_entity_names = set()
    unique_relations = set()
    processed_data = {
        'entities': {},
        'relations': []
    }

    # 处理实体
    if isinstance(data, dict) and 'entities' in data:
        entities = data['entities']
        if isinstance(entities, dict):
            for name, entity in entities.items():
                if name not in unique_entity_names:
                    processed_data['entities'][name] = entity
                    unique_entity_names.add(name)

    # 处理关系
    if isinstance(data, dict) and 'relations' in data:
        relations = data['relations']
        if isinstance(relations, list):
            for relation in relations:
                # 创建关系标识符，用于去重
                source = relation.get('source', '')
                target = relation.get('target', '')
                relation_type = relation.get('relation_type', '')

                if not (source and target and relation_type):
                    continue

                relation_key = f"{source}_{relation_type}_{target}"

                if relation_key not in unique_relations:
                    processed_data['relations'].append(relation)
                    unique_relations.add(relation_key)

    print(f"处理完成，去重后有 {len(processed_data['entities'])} 个实体和 {len(processed_data['relations'])} 个关系")
    return processed_data


def ensure_core_knowledge_points(data):
    """确保核心知识点存在于数据中"""
    print("确保核心知识点存在于知识图谱中...")

    # 如果数据为空，初始化
    if not data:
        data = {'entities': {}, 'relations': []}

    core_points_added = 0

    # 导入默认知识点数据
    try:
        sys.path.append(os.getcwd())
        from knowledgeGraph.apps.run import DEFAULT_KNOWLEDGE_DATA, DEFAULT_RELATIONS

        # 检查核心知识点是否存在
        for entity in DEFAULT_KNOWLEDGE_DATA:
            name = entity.get('name')
            if name in CORE_KNOWLEDGE_POINTS and name not in data['entities']:
                # 添加缺失的核心知识点
                data['entities'][name] = entity
                core_points_added += 1
                print(f"添加核心知识点: {name}")

        # 如果添加了任何核心知识点，也添加它们之间的关系
        if core_points_added > 0:
            # 记录已有的关系
            existing_relations = set()
            for relation in data['relations']:
                source = relation.get('source')
                target = relation.get('target')
                rel_type = relation.get('relation_type')
                if source and target and rel_type:
                    existing_relations.add(f"{source}_{rel_type}_{target}")

            # 添加默认关系
            relations_added = 0
            for relation in DEFAULT_RELATIONS:
                source = relation.get('source')
                target = relation.get('target')
                rel_type = relation.get('relation_type')

                # 只添加涉及核心知识点的关系，并且避免重复
                if (source in CORE_KNOWLEDGE_POINTS or target in CORE_KNOWLEDGE_POINTS) and \
                        f"{source}_{rel_type}_{target}" not in existing_relations:
                    data['relations'].append(relation)
                    relations_added += 1

            print(f"添加了 {relations_added} 个涉及核心知识点的关系")

    except ImportError:
        print("无法导入默认知识点数据，跳过添加核心知识点")

    print(f"共添加了 {core_points_added} 个核心知识点")
    return data


def save_mock_db_from_run():
    """从运行的程序中保存模拟数据库"""
    print("从运行程序中提取模拟数据库...")

    try:
        # 导入运行模块
        sys.path.append(os.getcwd())
        from run import KnowledgeGraphBuilder

        # 创建构建器实例
        builder = KnowledgeGraphBuilder(use_mock_db=True)

        # 检查是否有collector属性及其数据
        if hasattr(builder, 'collector'):
            mock_db = None
            if hasattr(builder.collector, 'mock_db'):
                mock_db = builder.collector.mock_db

            if mock_db:
                print(f"获取到内存数据库，保存中...")

                # 确保核心知识点存在
                mock_db = ensure_core_knowledge_points(mock_db)

                # 保存为pickle文件
                with open('knowledge_graph.pkl', 'wb') as f:
                    pickle.dump(mock_db, f)

                # 保存为JSON文件
                with open('knowledge_graph.json', 'w', encoding='utf-8') as f:
                    json.dump(mock_db, f, ensure_ascii=False, indent=2)

                print(f"数据库保存成功！")
                print(f"- 实体数量: {len(mock_db.get('entities', {}))} 个")
                print(f"- 关系数量: {len(mock_db.get('relations', []))} 个")
                return True
            else:
                print("未找到模拟数据库，尝试从其他地方获取数据...")
                return extract_data_from_collector()
        else:
            print("构建器没有collector属性，尝试从其他地方获取数据...")
            return extract_data_from_collector()
    except Exception as e:
        print(f"从run模块提取数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print("尝试从其他方式获取数据...")
        return extract_data_from_collector()


def extract_data_from_collector():
    """从数据采集器中提取数据"""
    try:
        print("尝试从采集器中提取数据...")
        from run import DataSourceCollector

        # 创建采集器实例
        collector = DataSourceCollector()

        # 提取已采集的数据
        if os.path.exists('data/collected_knowledge.json'):
            with open('data/collected_knowledge.json', 'r', encoding='utf-8') as f:
                collected_data = json.load(f)

            # 处理采集到的数据
            mock_db = {
                'entities': {},
                'relations': []
            }

            # 分批处理大规模数据
            batch_size = 1000
            entity_batch = {}
            relation_batch = []

            for i, item in enumerate(collected_data):
                if item.get('type') == 'entity':
                    entity_name = item.get('name')
                    if entity_name:
                        entity_batch[entity_name] = item
                elif item.get('type') == 'relation':
                    relation_batch.append(item)

                # 当批次达到一定大小时处理
                if (i + 1) % batch_size == 0:
                    # 处理实体批次
                    for name, entity in entity_batch.items():
                        mock_db['entities'][name] = entity

                    # 处理关系批次
                    mock_db['relations'].extend(relation_batch)

                    # 重置批次
                    entity_batch = {}
                    relation_batch = []

                    print(f"已处理 {i + 1}/{len(collected_data)} 条数据")

            # 处理最后一个批次
            for name, entity in entity_batch.items():
                mock_db['entities'][name] = entity
            mock_db['relations'].extend(relation_batch)

            # 检查是否有关系数据，如果没有，尝试从collected_data中提取相关主题生成关系
            if len(mock_db['relations']) == 0:
                print("未找到关系数据，尝试从实体的相关主题生成关系...")
                relation_count = 0

                for entity in collected_data:
                    if entity.get('type') == 'entity' and entity.get('properties'):
                        source_name = entity.get('name')
                        properties = entity.get('properties', {})

                        # 检查不同的可能的相关主题字段
                        related_topics = []

                        # 检查related_topics字段（数组形式）
                        if 'related_topics' in properties and isinstance(properties['related_topics'], list):
                            related_topics.extend(properties['related_topics'])

                        # 检查相关主题字段（字符串形式）
                        if '相关主题' in properties and isinstance(properties['相关主题'], str):
                            # 分割字符串并去除空格
                            topics = [topic.strip() for topic in properties['相关主题'].split(',')]
                            related_topics.extend(topics)

                        # 为每个相关主题创建关系
                        for target_name in related_topics:
                            # 跳过空目标或与源相同的目标
                            if not target_name or target_name == source_name:
                                continue

                            # 创建关系
                            relation = {
                                'type': 'relation',
                                'source': source_name,
                                'target': target_name,
                                'relation_type': 'RELATED_TO',
                                'source_type': 'derived_from_topics',
                                'confidence': 0.7,
                                'timestamp': entity.get('timestamp', '')
                            }
                            mock_db['relations'].append(relation)
                            relation_count += 1

                            # 每1000个关系输出一次进度
                            if relation_count % 1000 == 0:
                                print(f"已生成 {relation_count} 个关系")

                print(f"从相关主题生成了 {relation_count} 个关系")

            # 确保核心知识点存在
            mock_db = ensure_core_knowledge_points(mock_db)

            # 处理大规模数据集
            mock_db = process_large_dataset(mock_db)

            # 保存处理后的数据
            with open('knowledge_graph.pkl', 'wb') as f:
                pickle.dump(mock_db, f)

            with open('knowledge_graph.json', 'w', encoding='utf-8') as f:
                json.dump(mock_db, f, ensure_ascii=False, indent=2)

            print(f"从采集数据中提取成功！")
            print(f"- 实体数量: {len(mock_db.get('entities', {}))} 个")
            print(f"- 关系数量: {len(mock_db.get('relations', []))} 个")

            # 如果关系数量为0，建议运行generate_relations.py生成关系
            if len(mock_db['relations']) == 0:
                print("\n警告：未找到任何关系数据！")
                print("建议运行 python generate_relations.py 生成关系数据")

            return True
    except Exception as e:
        print(f"从采集器提取数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print("尝试从默认数据创建知识图谱...")
        return extract_from_default_data()


def extract_from_default_data():
    """从默认数据创建知识图谱"""
    try:
        from run import DEFAULT_COURSE_DATA, DEFAULT_KNOWLEDGE_DATA, DEFAULT_RELATIONS

        # 创建模拟数据库
        mock_db = {
            'entities': {},
            'relations': []
        }

        # 添加实体
        for entity in DEFAULT_COURSE_DATA + DEFAULT_KNOWLEDGE_DATA:
            if 'name' in entity:
                mock_db['entities'][entity['name']] = entity

        # 添加关系
        for relation in DEFAULT_RELATIONS:
            mock_db['relations'].append(relation)

        # 确保核心知识点存在
        mock_db = ensure_core_knowledge_points(mock_db)

        # 保存为pickle文件
        with open('knowledge_graph.pkl', 'wb') as f:
            pickle.dump(mock_db, f)

        # 保存为JSON文件
        with open('knowledge_graph.json', 'w', encoding='utf-8') as f:
            json.dump(mock_db, f, ensure_ascii=False, indent=2)

        print(f"从默认数据创建知识图谱成功！")
        print(f"- 实体数量: {len(mock_db.get('entities', {}))} 个")
        print(f"- 关系数量: {len(mock_db.get('relations', []))} 个")
        return True
    except Exception as e:
        print(f"从默认数据创建知识图谱失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def extract_from_json_file():
    """尝试从已有的JSON文件中加载数据"""
    try:
        print("尝试从已有的JSON文件中加载数据...")

        data_sources = []

        # 加载collected_knowledge.json
        if os.path.exists('data/collected_knowledge.json'):
            with open('data/collected_knowledge.json', 'r', encoding='utf-8') as f:
                collected_data = json.load(f)

            # 将数据转换为mock_db格式
            mock_db_from_collected = {
                'entities': {},
                'relations': []
            }

            for item in collected_data:
                if 'type' in item:
                    if item['type'] == 'entity' and 'name' in item:
                        mock_db_from_collected['entities'][item['name']] = item
                    elif item['type'] == 'relation':
                        mock_db_from_collected['relations'].append(item)

            data_sources.append(mock_db_from_collected)
            print(
                f"从collected_knowledge.json加载了 {len(mock_db_from_collected['entities'])} 个实体和 {len(mock_db_from_collected['relations'])} 个关系")

        # 如果存在existing_knowledge.json，也加载它
        if os.path.exists('data/existing_knowledge.json'):
            with open('data/existing_knowledge.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)

            # 添加到数据源列表
            data_sources.append(existing_data)
            print(
                f"从existing_knowledge.json加载了 {len(existing_data.get('entities', {}))} 个实体和 {len(existing_data.get('relations', []))} 个关系")

        # 如果有多个数据源，合并它们
        if len(data_sources) > 1:
            print("正在合并多个数据源...")
            mock_db = merge_entities_and_resolve_conflicts(data_sources)
        elif len(data_sources) == 1:
            mock_db = data_sources[0]
        else:
            print("没有找到任何有效的数据源")
            return False

        # 确保核心知识点存在
        mock_db = ensure_core_knowledge_points(mock_db)

        # 处理大规模数据集
        mock_db = process_large_dataset(mock_db)

        # 检查是否有关系数据，如果没有，尝试从related_topics生成关系
        if len(mock_db['relations']) == 0:
            print("未找到关系数据，尝试从实体的相关主题生成关系...")
            relation_count = 0

            for entity_name, entity in mock_db['entities'].items():
                properties = entity.get('properties', {})

                # 检查不同的可能的相关主题字段
                related_topics = []

                # 检查related_topics字段（数组形式）
                if 'related_topics' in properties and isinstance(properties['related_topics'], list):
                    related_topics.extend(properties['related_topics'])

                # 检查相关主题字段（字符串形式）
                if '相关主题' in properties and isinstance(properties['相关主题'], str):
                    # 分割字符串并去除空格
                    topics = [topic.strip() for topic in properties['相关主题'].split(',')]
                    related_topics.extend(topics)

                # 为每个相关主题创建关系
                for target_name in related_topics:
                    # 跳过空目标或与源相同的目标
                    if not target_name or target_name == entity_name:
                        continue

                    # 创建关系
                    relation = {
                        'type': 'relation',
                        'source': entity_name,
                        'target': target_name,
                        'relation_type': 'RELATED_TO',
                        'source_type': 'derived_from_topics',
                        'confidence': 0.7,
                        'timestamp': entity.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
                    }
                    mock_db['relations'].append(relation)
                    relation_count += 1

                    # 每1000个关系输出一次进度
                    if relation_count % 1000 == 0:
                        print(f"已生成 {relation_count} 个关系")

            print(f"从相关主题生成了 {relation_count} 个关系")

        # 保存为pickle文件和JSON文件
        with open('knowledge_graph.pkl', 'wb') as f:
            pickle.dump(mock_db, f)

        with open('knowledge_graph.json', 'w', encoding='utf-8') as f:
            json.dump(mock_db, f, ensure_ascii=False, indent=2)

        print(f"从JSON文件加载并保存成功！")
        print(f"- 实体数量: {len(mock_db.get('entities', {}))} 个")
        print(f"- 关系数量: {len(mock_db.get('relations', []))} 个")

        # 如果关系数量为0，建议运行generate_relations.py生成关系
        if len(mock_db['relations']) == 0:
            print("\n警告：未找到任何关系数据！")
            print("建议运行 python generate_relations.py 生成关系数据")

        return True
    except Exception as e:
        print(f"从JSON文件加载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("知识图谱数据保存工具")
    print("=" * 50)

    # 尝试多种方式保存图谱数据
    success = save_mock_db_from_run()

    if not success:
        success = extract_data_from_collector()

    if not success:
        success = extract_from_json_file()

    if not success:
        success = extract_from_default_data()

    if success:
        print("=" * 50)
        print("知识图谱数据保存成功！可以通过web_app.py查看")
        print("=" * 50)
    else:
        print("=" * 50)
        print("所有尝试都失败，无法保存知识图谱数据")
        print("=" * 50)
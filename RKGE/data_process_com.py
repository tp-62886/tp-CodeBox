import pandas as pd
import os
import numpy as np
from sklearn.decomposition import NMF
from sklearn.decomposition import TruncatedSVD
import argparse
from auxiliary_mapping_com import main as aux_main
from data_split_com import main as split_main
from negative_sample_com import main as neg_main
from path_extraction_com import main as path_main

def generate_pretrain_embedding(user_file_path, job_file_path, action_file_path, major_trans_path, user_embedding_path, item_embedding_path):
    # 加载数据
    user_data = pd.read_excel(user_file_path)
    job_data = pd.read_excel(job_file_path)
    action_data = pd.read_excel(action_file_path)

    # 加载行业映射
    DWHYMC_map = {}
    with open(major_trans_path, 'r', encoding='utf-8') as f:
        for line in f:
            original, mapped = line.strip().split()
            DWHYMC_map[original] = int(mapped)

    # 替换专业为映射后的值
    job_data['DWHYMC'] = job_data['DWHYMC'].map(DWHYMC_map)

    # 构建行业(DWHYMC) - 物品(学生)评分矩阵
    major_job_ratings = pd.merge(action_data, job_data[['DWZZJGDM', 'DWHYMC']], on='DWZZJGDM')
    major_job_matrix = pd.pivot_table(major_job_ratings, values='satisfied', index='DWHYMC', columns='SID', fill_value=0)

    # 使用SVD进行矩阵分解
    svd_model = TruncatedSVD(n_components=10, random_state=42)
    major_embeddings = svd_model.fit_transform(major_job_matrix)
    job_embeddings = svd_model.components_.T

    # 保存行业(DWHYMC)嵌入向量
    with open(user_embedding_path, 'w', encoding='utf-8') as f:
        for major, embedding in zip(major_job_matrix.index, major_embeddings):
            embedding_str = ' '.join(map(str, embedding))
            f.write(f'{major}|{embedding_str}\n')

    # 保存学生(SID)嵌入向量
    with open(item_embedding_path, 'w', encoding='utf-8') as f:
        for job, embedding in zip(major_job_matrix.columns, job_embeddings):
            embedding_str = ' '.join(map(str, embedding))
            f.write(f'{job}|{embedding_str}\n')

    print("Pre-train embedding file 处理完成。")

def generate_aux_file(file_path, output_path):
    # 读取Excel文件
    df = pd.read_excel(file_path)

    # 提取指定字段
    df_selected = df[['SID', 'DEPARTMENT', 'MAJOR', 'ZYFX']]

    # 保存为txt文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for index, row in df_selected.iterrows():
            line = f"id:{row['SID']}|DEPARTMENT:{row['DEPARTMENT']}|MAJOR:{row['MAJOR']}|ZYFX:{row['ZYFX']}\n"
            f.write(line)

    print("Auxiliary file 已保存为", output_path)

def generate_pretrain_embedding(user_file_path, job_file_path, action_file_path, major_trans_path, user_embedding_path, item_embedding_path):
    # 加载数据
    user_data = pd.read_excel(user_file_path)
    job_data = pd.read_excel(job_file_path)
    action_data = pd.read_excel(action_file_path)

    # 加载行业映射
    DWHYMC_map = {}
    with open(major_trans_path, 'r', encoding='utf-8') as f:
        for line in f:
            original, mapped = line.strip().split()
            DWHYMC_map[original] = int(mapped)

    # 替换专业为映射后的值
    job_data['DWHYMC'] = job_data['DWHYMC'].map(DWHYMC_map)

    # 构建行业(DWHYMC) - 物品(学生)评分矩阵
    major_job_ratings = pd.merge(action_data, job_data[['DWZZJGDM', 'DWHYMC']], on='DWZZJGDM')
    major_job_matrix = pd.pivot_table(major_job_ratings, values='satisfied', index='DWHYMC', columns='SID', fill_value=0)

    # 使用NMF进行矩阵分解
    nmf_model = NMF(n_components=10, init='random', random_state=42)
    major_embeddings = nmf_model.fit_transform(major_job_matrix)
    job_embeddings = nmf_model.components_.T

    # 保存行业(DWHYMC)嵌入向量
    with open(user_embedding_path, 'w', encoding='utf-8') as f:
        for major, embedding in zip(major_job_matrix.index, major_embeddings):
            embedding_str = ' '.join(map(str, embedding))
            f.write(f'{major}|{embedding_str}\n')

    # 保存学生(SID)嵌入向量
    with open(item_embedding_path, 'w', encoding='utf-8') as f:
        for job, embedding in zip(major_job_matrix.columns, job_embeddings):
            embedding_str = ' '.join(map(str, embedding))
            f.write(f'{job}|{embedding_str}\n')

    print("Pre-train embedding file 处理完成。")

def generate_interaction_file(user_file_path, action_file_path, major_trans_path, rating_output_path):
    # 读取用户数据
    user_df = pd.read_excel(user_file_path)

    # 创建MAJOR字段的映射
    major_unique = user_df['DWHYMC'].unique()
    major_mapping = {major: idx + 1 for idx, major in enumerate(major_unique)}

    # 保存映射关系到major_trans.txt
    with open(major_trans_path, 'w', encoding='utf-8') as f:
        for major, idx in major_mapping.items():
            f.write(f"{major} {idx}\n")

    # 读取操作数据
    action_df = pd.read_excel(action_file_path)

    # 合并数据
    merged_df = pd.merge(user_df[['DWZZJGDM', 'DWHYMC']], action_df[['SID', 'DWZZJGDM']], on='DWZZJGDM', how='inner')

    # 替换MAJOR字段值为映射值
    merged_df['DWHYMC'] = merged_df['DWHYMC'].map(major_mapping)

    # 保存结果到rating-delete-missing-itemid.txt
    with open(rating_output_path, 'w', encoding='utf-8') as f:
        for _, row in merged_df.iterrows():
            f.write(f"{row['DWHYMC']} {row['SID']}\n")

    print("文件处理完成。")

def data_process_job():

    parser = argparse.ArgumentParser(description='合并生成文件的步骤')

    parser.add_argument('--user_file_path', type=str, default='data/xdu/xdu_dataset_job.xlsx')
    parser.add_argument('--action_file_path', type=str, default='data/xdu/xdu_dataset_action.xlsx')
    parser.add_argument('--major_trans_path', type=str, default='data/xdu/DWHYMC_trans.txt')
    parser.add_argument('--rating_output_path', type=str, default='data/xdu/rating-delete-missing-itemid_com.txt')
    parser.add_argument('--auxiliary_file_path', type=str, default='data/xdu/xdu_dataset_user.xlsx')
    parser.add_argument('--auxiliary_output_path', type=str, default='data/xdu/auxiliary_com.txt')
    parser.add_argument('--user_embedding_path', type=str, default='data/xdu/pre-train-user-embedding_com.txt')
    parser.add_argument('--item_embedding_path', type=str, default='data/xdu/pre-train-item-embedding_com.txt')
    # todo 防止报错
    parser.add_argument('runserver', type=str)
    parser.add_argument('8000', type=int)

    args = parser.parse_args()

    generate_interaction_file(
        user_file_path=r"data\xdu\xdu_dataset_job.xlsx",
        action_file_path=r"data\xdu\xdu_dataset_action.xlsx",
        major_trans_path=r"data\xdu\DWHYMC_trans.txt",
        rating_output_path=r"data\xdu\rating-delete-missing-itemid_com.txt"
    )
    generate_aux_file(args.auxiliary_file_path, args.auxiliary_output_path)
    generate_pretrain_embedding(args.user_file_path, args.user_file_path, args.action_file_path, args.major_trans_path,
                                args.user_embedding_path, args.item_embedding_path)

    # 调用 auxiliary_mapping_com.py 的 main 函数
    aux_main('data/xdu/auxiliary_com.txt', 'data/xdu/auxiliary-mapping-com.txt')
    # 调用 data_split_com.py 的 main 函数
    split_main('data/xdu/rating-delete-missing-itemid_com.txt', 'data/xdu/training_com.txt', 'data/xdu/test_com.txt',
               0.8)
    # 调用 negative_sample_com.py 的 main 函数
    neg_main('data/xdu/training_com.txt', 'data/xdu/negative_com.txt', 0.05)
    # 调用 path_extraction_com.py 的 main 函数
    path_main('data/xdu/training_com.txt', 'data/xdu/negative_com.txt', 'data/xdu/auxiliary-mapping-com.txt',
              'data/xdu/positive-path_com.txt', 'data/xdu/negative-path_com.txt', 3, 5)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='合并生成文件的步骤')
#
#     parser.add_argument('--user_file_path', type=str, default='data/xdu/xdu_dataset_job.xlsx')
#     parser.add_argument('--action_file_path', type=str, default='data/xdu/xdu_dataset_action.xlsx')
#     parser.add_argument('--major_trans_path', type=str, default='data/xdu/DWHYMC_trans.txt')
#     parser.add_argument('--rating_output_path', type=str, default='data/xdu/rating-delete-missing-itemid_com.txt')
#     parser.add_argument('--auxiliary_file_path', type=str, default='data/xdu/xdu_dataset_user.xlsx')
#     parser.add_argument('--auxiliary_output_path', type=str, default='data/xdu/auxiliary_com.txt')
#     parser.add_argument('--user_embedding_path', type=str, default='data/xdu/pre-train-user-embedding_com.txt')
#     parser.add_argument('--item_embedding_path', type=str, default='data/xdu/pre-train-item-embedding_com.txt')
#
#     args = parser.parse_args()
#
#     generate_interaction_file(
#         user_file_path=r"data\xdu\xdu_dataset_job.xlsx",
#         action_file_path=r"data\xdu\xdu_dataset_action.xlsx",
#         major_trans_path=r"data\xdu\DWHYMC_trans.txt",
#         rating_output_path=r"data\xdu\rating-delete-missing-itemid_com.txt"
#     )
#     generate_aux_file(args.auxiliary_file_path, args.auxiliary_output_path)
#     generate_pretrain_embedding(args.user_file_path, args.user_file_path, args.action_file_path, args.major_trans_path,
#                                 args.user_embedding_path, args.item_embedding_path)
#
#
#     # 调用 auxiliary_mapping_com.py 的 main 函数
#     aux_main('data/xdu/auxiliary_com.txt', 'data/xdu/auxiliary-mapping-com.txt')
#     # 调用 data_split_com.py 的 main 函数
#     split_main('data/xdu/rating-delete-missing-itemid_com.txt', 'data/xdu/training_com.txt', 'data/xdu/test_com.txt', 0.8)
#     # 调用 negative_sample_com.py 的 main 函数
#     neg_main('data/xdu/training_com.txt', 'data/xdu/negative_com.txt', 0.05)
#     # 调用 path_extraction_com.py 的 main 函数
#     path_main('data/xdu/training_com.txt', 'data/xdu/negative_com.txt', 'data/xdu/auxiliary-mapping-com.txt',
#               'data/xdu/positive-path_com.txt', 'data/xdu/negative-path_com.txt', 3, 5)
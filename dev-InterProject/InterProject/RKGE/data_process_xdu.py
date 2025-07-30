import pandas as pd
import numpy as np
import os
from sklearn.decomposition import NMF
from sklearn.decomposition import TruncatedSVD
from RKGE.auxiliary_mapping_xdu import main as aux_main
from RKGE.data_split_xdu import main as split_main
from RKGE.negative_sample_xdu import main as neg_main
from RKGE.path_extraction_xdu import main as path_main


def data_process_student():
    # 数据预处理##############################################################################
    # Define file paths
    user_file_path = r"data/xdu/xdu_dataset_user.xlsx"
    action_file_path = r"data/xdu/xdu_dataset_action.xlsx"
    job_file_path = r"data/xdu/xdu_dataset_job.xlsx"
    major_trans_path = r"data/xdu/major_trans.txt"
    rating_output_path = r"data/xdu/rating-delete-missing-itemid.txt"
    auxiliary_output_path = r"data/xdu/auxiliary.txt"
    user_embedding_output_path = r"data\xdu\pre-train-user-embedding.txt"
    item_embedding_output_path = r"data\xdu\pre-train-item-embedding.txt"

    # Step 1: Process user data and create major mapping
    user_df = pd.read_excel(user_file_path)
    major_unique = user_df['MAJOR'].unique()
    major_mapping = {major: idx + 1 for idx, major in enumerate(major_unique)}

    with open(major_trans_path, 'w', encoding='utf-8') as f:
        for major, idx in major_mapping.items():
            f.write(f"{major} {idx}\n")

    # Step 2: Process action data and merge with user data
    action_df = pd.read_excel(action_file_path, dtype={"SID": str, "DWZZJGDM": str})
    merged_df = pd.merge(user_df[['SID', 'MAJOR']], action_df[['SID', 'DWZZJGDM']], on='SID', how='inner')
    merged_df['MAJOR'] = merged_df['MAJOR'].map(major_mapping)
    with open(rating_output_path, 'w', encoding='utf-8') as f:
        for _, row in merged_df.iterrows():
            f.write(f"{row['MAJOR']} {row['DWZZJGDM']}\n")

    print("Step 2: Rating data processed and saved.")

    # Step 3: Process job data and save auxiliary information
    job_df = pd.read_excel(job_file_path)
    df_selected = job_df[['DWZZJGDM', 'DWHYMC', 'DWXZMC', 'GZZWLBMC']]

    with open(auxiliary_output_path, 'w', encoding='utf-8') as f:
        for index, row in df_selected.iterrows():
            line = f"id:{row['DWZZJGDM']}|DWHYMC:{row['DWHYMC']}|DWXZMC:{row['DWXZMC']}|GZZWLBMC:{row['GZZWLBMC']}\n"
            f.write(line)

    print("Step 3: Auxiliary data processed and saved.")

    ###################################################嵌入预训练部分#####################################################
    # 加载数据
    user_data = pd.read_excel('data/xdu/xdu_dataset_user.xlsx')
    job_data = pd.read_excel('data/xdu/xdu_dataset_job.xlsx')
    action_data = pd.read_excel('data/xdu/xdu_dataset_action.xlsx', dtype={"SID": str, "DWZZJGDM": str})
    # 加载专业映射
    major_map = {}
    with open('data/xdu/major_trans.txt', 'r', encoding='utf-8') as f:
        for line in f:
            original, mapped = line.strip().split()
            # words = line.strip().split()
            # if len(words) > 2:
            #     print(words)
            #     original = words[0]
            #     mapped = words[len(words) - 1]
            # else:
            #     original, mapped = words[0], words[1]
            major_map[original] = int(mapped)

    # 替换专业为映射后的值
    user_data['MAJOR'] = user_data['MAJOR'].map(major_map)

    # 构建专业(MAJOR) - 物品(工作)评分矩阵
    major_job_ratings = pd.merge(action_data, user_data[['SID', 'MAJOR']], on='SID')
    major_job_matrix = pd.pivot_table(major_job_ratings, values='satisfied', index='MAJOR', columns='DWZZJGDM',
                                      fill_value=0)

    # 使用SVD进行矩阵分解
    svd = TruncatedSVD(n_components=15, random_state=42)
    major_embeddings = svd.fit_transform(major_job_matrix)
    job_embeddings = svd.components_.T

    # 保存专业(MAJOR)嵌入向量
    with open('data/xdu/pre-train-user-embedding.txt', 'w', encoding='utf-8') as f:
        for major, embedding in zip(major_job_matrix.index, major_embeddings):
            embedding_str = ' '.join(map(str, embedding))
            f.write(f'{major}|{embedding_str}\n')

    # 保存工作(物品)嵌入向量
    with open('data/xdu/pre-train-item-embedding.txt', 'w', encoding='utf-8') as f:
        for job, embedding in zip(major_job_matrix.columns, job_embeddings):
            embedding_str = ' '.join(map(str, embedding))
            f.write(f'{job}|{embedding_str}\n')

    # # Step 4: Perform NMF for embeddings
    # user_data = pd.read_excel(user_file_path)
    # action_data = pd.read_excel(action_file_path)
    #
    # major_map = {}
    # with open(major_trans_path, 'r', encoding='utf-8') as f:
    #     for line in f:
    #         original, mapped = line.strip().split()
    #         major_map[original] = int(mapped)
    #
    # user_data['MAJOR'] = user_data['MAJOR'].map(major_map)
    # major_job_ratings = pd.merge(action_data, user_data[['SID', 'MAJOR']], on='SID')
    # major_job_matrix = pd.pivot_table(major_job_ratings, values='satisfied', index='MAJOR', columns='DWZZJGDM', fill_value=0)
    #
    #
    # nmf_model = NMF(n_components=10, init='random', random_state=42)
    # major_embeddings = nmf_model.fit_transform(major_job_matrix)
    # job_embeddings = nmf_model.components_.T
    #
    # with open(user_embedding_output_path, 'w', encoding='utf-8') as f:
    #     for major, embedding in zip(major_job_matrix.index, major_embeddings):
    #         embedding_str = ' '.join(map(str, embedding))
    #         f.write(f'{major}|{embedding_str}\n')
    #
    # with open(item_embedding_output_path, 'w', encoding='utf-8') as f:
    #     for job, embedding in zip(major_job_matrix.columns, job_embeddings):
    #         embedding_str = ' '.join(map(str, embedding))
    #         f.write(f'{job}|{embedding_str}\n')
    #
    # print("Step 4: Embeddings processed and saved.")

    # 数据处理########################################################################################

    # 调用 auxiliary_mapping_xdu.py 的 main 函数
    aux_main('data/xdu/auxiliary.txt', 'data/xdu/auxiliary-mapping.txt')

    # 调用 data_split_xdu.py 的 main 函数
    split_main('data/xdu/rating-delete-missing-itemid.txt', 'data/xdu/training.txt', 'data/xdu/test.txt', 0.8)

    # 调用 negative_sample_xdu.py 的 main 函数
    neg_main('data/xdu/training.txt', 'data/xdu/negative.txt', 0.05)  # 可以设置负采样比例为0.025或者其他值

    # 调用 path_extraction_xdu.py 的 main 函数
    path_main('data/xdu/training.txt', 'data/xdu/negative.txt', 'data/xdu/auxiliary-mapping.txt',
              'data/xdu/positive-path.txt', 'data/xdu/negative-path.txt', 3, 5)

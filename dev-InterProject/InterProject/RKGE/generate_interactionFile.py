import pandas as pd
import os

# 文件路径
user_file_path = r"data\xdu\xdu_dataset_user.xlsx"
action_file_path = r"data\xdu\xdu_dataset_action.xlsx"
major_trans_path = r"data\xdu\major_trans.txt"
rating_output_path = r"data\xdu\rating-delete-missing-itemid.txt"

# 读取用户数据
user_df = pd.read_excel(user_file_path)

# 创建MAJOR字段的映射
major_unique = user_df['MAJOR'].unique()
major_mapping = {major: idx + 1 for idx, major in enumerate(major_unique)}

# 保存映射关系到major_trans.txt
with open(major_trans_path, 'w', encoding='utf-8') as f:
    for major, idx in major_mapping.items():
        f.write(f"{major} {idx}\n")

# 读取操作数据
action_df = pd.read_excel(action_file_path)

# 合并数据
merged_df = pd.merge(user_df[['SID', 'MAJOR']], action_df[['SID', 'DWZZJGDM']], on='SID', how='inner')

# 替换MAJOR字段值为映射值
merged_df['MAJOR'] = merged_df['MAJOR'].map(major_mapping)

# 保存结果到rating-delete-missing-itemid.txt
with open(rating_output_path, 'w', encoding='utf-8') as f:
    for _, row in merged_df.iterrows():
        f.write(f"{row['MAJOR']} {row['DWZZJGDM']}\n")

print("文件处理完成。")

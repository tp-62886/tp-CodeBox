import os

import pandas as pd

def append_unique_entries(original_file, increment_file, key_column,file_type):
    """
    将增量文件中的数据追加到原文件中，如果key_column字段不在原文件中出现过。

    参数:
    original_file (str): 原文件的路径。
    increment_file (str): 增量文件的路径。
    key_column (str): 用于筛选的关键字段。
    output_file (str): 输出文件的路径。
    """
    if file_type == 'ivec' or file_type == 'uvec':
        delimiter = ','
        delimiter
    else:
        delimiter = '\t'

    # 读取原文件和追加文件
    original_df = pd.read_csv(original_file, delimiter=delimiter)
    increment_df = pd.read_csv(increment_file, delimiter=delimiter)

    if file_type == 'inter':
        result_df = pd.concat([original_df, increment_df])
    else:
        # 获取原文件中的所有key_column
        original_keys = set(original_df[key_column])

        # 筛选增量文件中key_column不在原文件中的数据
        filtered_increment_df = increment_df[~increment_df[key_column].isin(original_keys)]

        # 将筛选后的数据追加到原文件中
        result_df = pd.concat([original_df, filtered_increment_df])

    # 保存结果到输出文件
    result_df.to_csv(original_file, index=False, sep=delimiter)




base_dir = r'D:\1-work-code\JobRecProject_v2\JobRec\dataset'
zhilian_dir = os.path.join(base_dir, 'xdu')
increment_dir = os.path.join(base_dir, 'xdu_incre')
file_types = ['inter', 'ivec', 'uvec', 'user', 'idoc', 'udoc']
filter_fields = {'inter':'user_id:token', 'ivec':'job_id', 'uvec':'user_id',
                 'user':'SID:token', 'idoc':'job_id:token', 'udoc':'user_id:token'}

# 遍历文件类型并进行合并
for file_type in file_types:
    # 构建文件路径
    zhilian_file = os.path.join(zhilian_dir, f'xdu.{file_type}')
    increment_file = os.path.join(increment_dir, f'xdu_incre.{file_type}')

    # 检查文件是否存在
    if os.path.exists(zhilian_file) and os.path.exists(increment_file):
        append_unique_entries(zhilian_file, increment_file, filter_fields[file_type],file_type)
        print(f'Successfully appended {increment_file} to {zhilian_file} without duplicates.')
    else:
        print(f'File {zhilian_file} or {increment_file} does not exist.')


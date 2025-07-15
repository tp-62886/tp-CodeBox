import os

# 定义文件路径
base_dir = r'D:\pythonProject2\JobRecProject\JobRec\dataset'
zhilian_dir = os.path.join(base_dir, 'xdu')
increment_dir = os.path.join(base_dir, 'xdu_Increment')

# 定义要合并的文件类型
file_types = ['inter', 'item', 'idoc', 'ivec']

# 遍历文件类型并进行合并
for file_type in file_types:
    # 构建文件路径
    zhilian_file = os.path.join(zhilian_dir, f'xdu.{file_type}')
    increment_file = os.path.join(increment_dir, f'xdu_Increment.{file_type}')

    # 检查文件是否存在
    if os.path.exists(zhilian_file) and os.path.exists(increment_file):
        # 打开文件并读取内容
        with open(zhilian_file, 'a', encoding='utf-8') as zf, open(increment_file, 'r', encoding='utf-8') as inf:
            # 跳过增量文件的标题行
            next(inf)
            # 将增量文件的内容追加到原始文件
            for line in inf:
                zf.write(line)
        print(f'Successfully appended {increment_file} to {zhilian_file}')
    else:
        print(f'File {zhilian_file} or {increment_file} does not exist.')

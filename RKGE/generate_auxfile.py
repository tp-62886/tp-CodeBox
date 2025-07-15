import pandas as pd
import os
#########################################################  处理原表，形成auxiliary.txt######################################
# 读取Excel文件
file_path = r"data\xdu\xdu_dataset_job.xlsx"
df = pd.read_excel(file_path)

# 提取指定字段
df_selected = df[['DWZZJGDM', 'DWHYMC', 'DWXZMC', 'GZZWLBMC']]

# 保存为txt文件
output_path = r"data\xdu\auxiliary.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    for index, row in df_selected.iterrows():
        line = f"id:{row['DWZZJGDM']}|DWHYMC:{row['DWHYMC']}|DWXZMC:{row['DWXZMC']}|GZZWLBMC:{row['GZZWLBMC']}\n"
        f.write(line)

print("文件已保存为", output_path)

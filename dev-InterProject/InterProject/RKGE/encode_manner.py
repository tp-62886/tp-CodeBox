import chardet

# 检测文件编码
with open('data/xdu/results_com.txt', 'rb') as f:
    raw_data = f.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    print(encoding)

# # 使用检测到的编码打开文件
# with open('filename.txt', 'r', encoding=encoding) as f:
#     content = f.read()

import pandas as pd
import json
import random


def get_recommendation(CID):
    # 读取 xdu_dataset_user.xlsx
    job_df = pd.read_excel('data/xdu/xdu_dataset_job.xlsx')
    # print(type(user_df['SID'][0]))
    # 根据 SID 获取 MAJOR 字段值
    job_row = job_df[job_df['DWZZJGDM'] == CID]
    if job_row.empty:
        print("没有找到对应公司信息")
        return
    else:
        print("已找到对应公司信息")

    DWHYMC = job_row['DWHYMC'].values[0]

    # 读取 major_trans.txt
    with open('data/xdu/DWHYMC_trans.txt', 'r', encoding='utf-8') as f:
        DWHYMC_trans = dict(line.strip().split(' ') for line in f)

    # 获取映射后的 MAJOR 值
    mapped_DWHYMC = DWHYMC_trans.get(DWHYMC)
    if not mapped_DWHYMC:
        print("没有找到对应行业映射信息")
        return
    else:
        print("已找到对应行业映射信息")

    # 读取 recommend_result_com 文件
    with open('data/xdu/recommend_result_com', 'r') as f:
        recommend_result = json.load(f)

    # 获取推荐列表
    recommend_list = recommend_result.get(mapped_DWHYMC)
    if not recommend_list:
        print("没有找到对应的推荐列表")
        return
    else:
        print("已获取对应推荐列表")

    # 取推荐列表长度和10的较小值
    random.shuffle(recommend_list)
    top_n = min(len(recommend_list), 10)
    top_recommendations = recommend_list[:top_n]

    # 读取 xdu_dataset_job.xlsx
    user_df = pd.read_excel('data/xdu/xdu_dataset_user.xlsx')

    # 打印推荐结果
    for rec in top_recommendations:
        # print(rec)
        user_info = user_df[user_df['SID'] == int(rec)]
        if not user_info.empty:
            print(user_info.to_string(index=False))


if __name__ == "__main__":
    # 从键盘读取 SID
    CID = input("请输入公司ID: ")
    # print(type(SID))
    get_recommendation(CID)

# 91650000MA7781KU5D

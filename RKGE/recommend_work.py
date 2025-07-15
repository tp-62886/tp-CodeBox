import pandas as pd
import json
import random


def get_recommendation(SID):
    # 读取 xdu_dataset_user.xlsx
    user_df = pd.read_excel('data/xdu/xdu_dataset_user.xlsx')
    # print(type(user_df['SID'][0]))
    # 根据 SID 获取 MAJOR 字段值
    user_row = user_df[user_df['SID'] == SID]
    if user_row.empty:
        print("没有找到对应的学生信息")
        return
    else:
        print("已找到对应的学生信息")

    major = user_row['MAJOR'].values[0]

    # 读取 major_trans.txt
    with open('data/xdu/major_trans.txt', 'r', encoding='utf-8') as f:
        major_trans = dict(line.strip().split(' ') for line in f)

    # 获取映射后的 MAJOR 值
    mapped_major = major_trans.get(major)
    if not mapped_major:
        print("没有找到对应的专业映射信息")
        return
    else:
        print("已找到对应的专业映射信息")

    # 读取 recommend_result 文件
    with open('data/xdu/recommend_result', 'r') as f:
        recommend_result = json.load(f)

    # 获取推荐列表
    recommend_list = recommend_result.get(mapped_major)
    if not recommend_list:
        print("没有找到对应的推荐列表")
        return
    else:
        print("已获取对应推荐列表")

    # 取推荐列表长度和10的较小值

    random.shuffle(recommend_list)  # 2024——7——17，增加随机获取推荐列表中推荐项目功能

    top_n = min(len(recommend_list), 10)
    top_recommendations = recommend_list[:top_n]

    # 读取 xdu_dataset_job.xlsx
    job_df = pd.read_excel('data/xdu/xdu_dataset_job.xlsx')

    # 打印推荐结果
    for rec in top_recommendations:
        job_info = job_df[job_df['DWZZJGDM'] == rec]
        if not job_info.empty:
            print(job_info.to_string(index=False))


if __name__ == "__main__":
    # 从键盘读取 SID
    SID = int(input("请输入学生学号: "))
    # print(type(SID))
    get_recommendation(SID)

# 20051212160

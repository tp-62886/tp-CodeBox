# This is part is aims to feed connected paths into the recurrent neural network to train and test the proposed methods.

import numpy as np
import pandas as pd
import heapq
import argparse
import torch
import torch.autograd as autograd
from torch import nn, optim
from torch.autograd import Variable
import torch.nn.functional as F
import RKGE.LSTMTrain
from RKGE.LSTMTagger import LSTMTagger
from RKGE.LSTMTrain import LSTMTrain
from RKGE.LSTMEvaluation import LSTMEvaluation
from datetime import datetime
import os
import json


def load_paths(fr_file, isPositive, node_count, all_variables, paths_between_pairs, positive_label, all_user,
               all_movie):
    '''
    load postive or negative paths, map all nodes in paths into ids

    Inputs:
        @fr_file: positive or negative paths
        @isPositive: identify fr_file is positive or negative
    '''

    # global node_count, all_variables, paths_between_pairs, positive_label, all_user, all_movie

    for line in fr_file:
        line = line.replace('\n', '')
        lines = line.split(',')
        user = lines[0]
        movie = lines[-1]

        if user not in all_user:
            all_user.append(user)
        if movie not in all_movie:
            all_movie.append(movie)

        key = (user, movie)
        value = []
        path = []

        if isPositive:
            if key not in positive_label:
                positive_label.append(key)

        for node in lines:
            if node not in all_variables:
                all_variables.update({node: node_count})
                node_count = node_count + 1
            path.append(node)

        if key not in paths_between_pairs:
            value.append(path)
            paths_between_pairs.update({key: value})
        else:
            paths_between_pairs[key].append(path)


def load_pre_embedding(fr_pre_file, isUser, pre_embedding, all_variables):
    '''
    load pre-train-user or movie embeddings

    Inputs:
        @fr_pre_file: pre-train-user or -movie embeddings
        @isUser: identify user or movie
    '''
    # global pre_embedding, all_variables

    expected_dim = 10  # 期望的嵌入向量维度

    for line in fr_pre_file:
        lines = line.split('|')
        node = lines[0]
        if isUser:
            node = 'u' + node
        else:
            node = 'i' + node  # 检查i+node中的node是数字标识还是原excel中对应的一串字符串标识

        if node in all_variables:
            node_id = all_variables[node]
            embedding = [float(x) for x in lines[1].split()]
            embedding = np.array(embedding)
            # 检查并调整嵌入向量的维度
            if embedding.shape[0] > expected_dim:
                embedding = embedding[:expected_dim]
            elif embedding.shape[0] < expected_dim:
                embedding = np.pad(embedding, (0, expected_dim - embedding.shape[0]), 'constant')

            pre_embedding[node_id] = embedding


def load_data(fr_file):
    '''
    load training or test data

    Input:
            @fr_rating: the user-item rating data

    Output:
            @rating_data: user-specific rating data with timestamp
    '''

    data_dict = {}

    for line in fr_file:
        lines = line.replace('\n', '').split(' ')
        user = 'u' + lines[0]
        item = 'i' + lines[1]

        if user not in data_dict:
            data_dict.update({user: [item]})
        elif item not in data_dict[user]:
            data_dict[user].append(item)

    return data_dict


def write_results(fw_results, precision_1, precision_5, precision_10, mrr_10):
    '''
    write results into text file
    '''
    line = 'precision@1: ' + str(precision_1) + '\n' + 'precision@5: ' + str(precision_5) + '\n' \
           + 'precision@10: ' + str(precision_10) + '\n' + 'mrr: ' + str(mrr_10) + '\n'
    fw_results.write(line)


##################以下函数为读取学号并给出推荐列表的功能函数##################################################################################
def get_student_major(sid):
    # 读取用户信息表
    df_users = pd.read_excel('data/xdu/xdu_dataset_user.xlsx')
    student_row = df_users[df_users['SID'] == sid]
    if not student_row.empty:
        return student_row.iloc[0]['MAJOR']
    else:
        return None


def get_mapped_major(major):
    # 读取专业映射文件
    with open('major_trans.txt', 'r') as f:
        for line in f:
            original, mapped = line.strip().split(',')
            if original == major:
                return mapped
    return None


def get_recommendations(mapped_major, top_score_dict, all_movie):
    # 获取前10个推荐物品的DWZZJGDM字段值
    if mapped_major in top_score_dict:
        candidate_item = top_score_dict[mapped_major]
        return candidate_item[:10]
    return []


def get_job_info(dwzzjgdm_list):
    # 读取工作信息表
    df_jobs = pd.read_excel('data/xdu/xdu_dataset_job.xlsx')
    recommended_jobs = df_jobs[df_jobs['DWZZJGDM'].isin(dwzzjgdm_list)]
    return recommended_jobs


# def recommend(top_score_dict, all_movie):
#     sid = input("请输入学生的学号: ")
#
#     major = get_student_major(sid)
#     if not major:
#         print(f"未找到学号为 {sid} 的学生信息。")
#         return
#
#     mapped_major = get_mapped_major(major)
#     if not mapped_major:
#         print(f"未找到专业 {major} 的映射信息。")
#         return
#
#     recommendations = get_recommendations(mapped_major, top_score_dict, all_movie)
#     if not recommendations:
#         print(f"未找到专业 {mapped_major} 的推荐信息。")
#         return
#
#     job_info = get_job_info(recommendations)
#     if job_info.empty:
#         print(f"未找到推荐的工作信息。")
#     else:
#         print("推荐的工作信息如下：")
#         print(job_info)


def train_student_model():
    parser = argparse.ArgumentParser(description=''' Recurrent Neural Network ''')

    '''
    Parameter Settings: 
    for MovieLens in terms of [input_dim, hidden_dim, out_dim, iteration, learning_rate, optimizer] is [10, 16, 1, 5, 0.2/0.1, SGD]
    for Yelp in terms of [input_dim, hidden_dim, out_dim, iteration, learning_rate, optimizer] is [20, 32, 1, 5, 0.01, SGD]
    You can change optimizer in the LSTMTrain class
    '''

    parser.add_argument('--inputdim', type=int, dest='input_dim', default=10)
    parser.add_argument('--hiddendim', type=int, dest='hidden_dim', default=32)
    parser.add_argument('--outdim', type=int, dest='out_dim', default=1)
    parser.add_argument('--iteration', type=int, dest='iteration', default=1)
    parser.add_argument('--learingrate', type=float, dest='learning_rate', default=0.1)

    parser.add_argument('--positivepath', type=str, dest='positive_path', default='data/xdu/positive-path.txt')
    parser.add_argument('--negativepath', type=str, dest='negative_path', default='data/xdu/negative-path.txt')
    parser.add_argument('--pretrainuserembedding', type=str, dest='pre_train_user_embedding',
                        default='data/xdu/pre-train-user-embedding.txt')
    parser.add_argument('--pretrainmovieembedding', type=str, dest='pre_train_movie_embedding',
                        default='data/xdu/pre-train-item-embedding.txt')
    parser.add_argument('--train', type=str, dest='train_file', default='data/xdu/training.txt')
    parser.add_argument('--test', type=str, dest='test_file', default='data/xdu/test.txt')
    parser.add_argument('--results', type=str, dest='results', default='data/xdu/results.txt')
    # todo 防止报错
    parser.add_argument('runserver', type=str)
    parser.add_argument('8000', type=int)
    # todo 报错
    parsed_args = parser.parse_args()

    input_dim = parsed_args.input_dim
    hidden_dim = parsed_args.hidden_dim
    out_dim = parsed_args.out_dim
    iteration = parsed_args.iteration
    learning_rate = parsed_args.learning_rate

    positive_path = parsed_args.positive_path
    negative_path = parsed_args.negative_path
    pre_train_user_embedding = parsed_args.pre_train_user_embedding
    pre_train_movie_embedding = parsed_args.pre_train_movie_embedding
    train_file = parsed_args.train_file  # 专业-工作交互记录
    test_file = parsed_args.test_file
    results_file = parsed_args.results

    start_time = datetime.now()

    fr_postive = open(positive_path, 'r')
    fr_negative = open(negative_path, 'r')
    fr_pre_user = open(pre_train_user_embedding, 'r')
    fr_pre_movie = open(pre_train_movie_embedding, 'r')
    fr_train = open(train_file, 'r', encoding='Windows-1252')
    fr_test = open(test_file, 'r')
    fw_results = open(results_file, 'w')

    node_count = 0  # count the number of all entities (user, movie and attributes)
    all_variables = {}  # save variable and corresponding id
    paths_between_pairs = {}  # save all the paths (both positive and negative) between a user-movie pair
    positive_label = []  # save the positive user-movie pairs
    all_user = []  # save all the users
    all_movie = []  # save all the movies

    start_time = datetime.now()
    load_paths(fr_postive, True, node_count, all_variables, paths_between_pairs, positive_label, all_user, all_movie)
    load_paths(fr_negative, False, node_count, all_variables, paths_between_pairs, positive_label, all_user, all_movie)
    print('The number of all variables is :' + str(len(all_variables)))
    end_time = datetime.now()
    duration = end_time - start_time
    print('the duration for loading user path is ' + str(duration) + '\n')

    start_time = datetime.now()
    node_size = len(all_variables)
    pre_embedding = np.random.rand(node_size, input_dim)  # embeddings for all nodes
    load_pre_embedding(fr_pre_user, True, pre_embedding, all_variables)
    load_pre_embedding(fr_pre_movie, False, pre_embedding, all_variables)
    pre_embedding = torch.FloatTensor(pre_embedding)
    end_time = datetime.now()
    duration = end_time - start_time
    print('the duration for loading embedding is ' + str(duration) + '\n')

    start_time = datetime.now()
    model = LSTMTagger(node_size, input_dim, hidden_dim, out_dim, pre_embedding)
    if torch.cuda.is_available():
        model = model.cuda()

    model_train = LSTMTrain(model, iteration, learning_rate, paths_between_pairs, positive_label, \
                            all_variables, all_user, all_movie)
    embedding_dict = model_train.train()
    print('model training finished')
    end_time = datetime.now()
    duration = end_time - start_time
    print('the duration for model training is ' + str(duration) + '\n')

    start_time = datetime.now()
    train_dict = load_data(fr_train)
    test_dict = load_data(fr_test)
    model_evaluation = LSTMEvaluation(embedding_dict, all_movie, train_dict, test_dict)
    top_score_dict = model_evaluation.calculate_ranking_score()

    model_evaluation = LSTMEvaluation(embedding_dict, all_movie, train_dict, test_dict)
    top_score_dict = model_evaluation.calculate_ranking_score()
    precision_1, _ = model_evaluation.calculate_results(top_score_dict, 1)
    precision_5, _ = model_evaluation.calculate_results(top_score_dict, 5)
    precision_10, mrr_10 = model_evaluation.calculate_results(top_score_dict, 10)
    end_time = datetime.now()
    duration = end_time - start_time
    print('the duration for model evaluation is ' + str(duration) + '\n')

    # #################################保存学生的推荐列表#############################################################
    # 创建结果字典
    recommend_result = {}
    for user, items in top_score_dict.items():
        new_user = user.lstrip('u')
        new_items = [item.lstrip('i') for item in items]
        recommend_result[new_user] = new_items

    # 确保目录存在
    os.makedirs('data/xdu', exist_ok=True)

    # 保存到文件
    with open('data/xdu/recommend_result', 'w') as f:
        json.dump(recommend_result, f, indent=4)
    # 保存推荐结果，在其他程序中利用该结果进行推荐

    ########################################################################################################################
    write_results(fw_results, precision_1, precision_5, precision_10, mrr_10)

    end_time = datetime.now()
    duration = end_time - start_time
    print('the duration for loading item embedding is ' + str(duration) + '\n')

    fr_postive.close()
    fr_negative.close()
    fr_pre_user.close()
    fr_pre_movie.close()
    fr_train.close()
    fr_test.close()
    fw_results.close()

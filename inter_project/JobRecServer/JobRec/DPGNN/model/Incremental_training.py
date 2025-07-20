import os

import torch
import yaml
from JobRec.DPGNN.model.dpgnn import DPGNN
import pandas as pd
from JobRec.DPGNN.Utils.config import PJFConfig
from JobRec.DPGNN.Dataset.dataset import PJFDataset
from JobRec.DPGNN.Dataset.utils import data_preparation
from recbole.utils import init_logger, init_seed, set_color
from JobRec.DPGNN.Utils.utils import get_trainer
import torch
import torch.nn as nn
import numpy as np
from scipy.sparse import coo_matrix

def load_trained_model(config, model_file_path):
    dataset = PJFDataset(config)
    train_data, valid_data, test_data = data_preparation(config, dataset)
    model = DPGNN(config, train_data.dataset).to(config['device'])
    # 加载训练好的模型权重
    checkpoint = torch.load(model_file_path, map_location=config['device'])
    # 使用 torch.load 加载模型检查点，并将状态字典和其他参数加载到模型中
    model.load_state_dict(checkpoint["state_dict"])
    model.load_other_parameter(checkpoint.get("other_parameter"))
    return model, valid_data

'''更新嵌入层'''
def initialize_new_embeddings(model, num_new_users, new_num_items):
    # 获取预训练嵌入
    old_user_embedding_a = model.user_embedding_a
    old_item_embedding_a = model.item_embedding_a
    old_user_embedding_p = model.user_embedding_p
    old_item_embedding_p = model.item_embedding_p

    # 更新用户、物品数量
    new_num_users = model.n_users + num_new_users
    new_num_items = model.n_items + new_num_items

    # 初始化新嵌入
    new_user_embedding_a = nn.Embedding(new_num_users, model.latent_dim)
    new_item_embedding_a = nn.Embedding(new_num_items, model.latent_dim)
    new_user_embedding_p = nn.Embedding(new_num_users, model.latent_dim)
    new_item_embedding_p = nn.Embedding(new_num_items, model.latent_dim)

    # 复制原有用户、物品的嵌入
    with torch.no_grad():
        new_user_embedding_a.weight[:model.n_users] = old_user_embedding_a.weight
        new_item_embedding_a.weight[:model.n_items] = old_item_embedding_a.weight
        new_user_embedding_p.weight[:model.n_users] = old_user_embedding_p.weight
        new_item_embedding_p.weight[:model.n_items] = old_item_embedding_p.weight

    # 初始化新用户的嵌入
    nn.init.xavier_normal_(new_user_embedding_a.weight[model.n_users:])
    nn.init.xavier_normal_(new_item_embedding_a.weight[model.n_items:])
    nn.init.xavier_normal_(new_user_embedding_p.weight[model.n_users:])
    nn.init.xavier_normal_(new_item_embedding_p.weight[model.n_items:])

    model.user_embedding_a = new_user_embedding_a
    model.item_embedding_a = new_item_embedding_a
    model.user_embedding_p = new_user_embedding_p
    model.item_embedding_p = new_item_embedding_p

    # 更新用户和项目的数量
    model.n_users = new_num_users
    model.n_items = new_num_items

'''更新交互矩阵并重新计算邻接矩阵并更新模型'''
def update_interaction_matrices(model, new_dataset):
    # 获取现有的交互矩阵
    existing_interaction_matrix = model.interaction_matrix
    existing_user_add_matrix = model.user_add_matrix
    existing_job_add_matrix = model.job_add_matrix

    # 获取增量数据的交互矩阵
    new_interaction_matrix = new_dataset.inter_matrix(form='coo').astype(np.float32)
    new_user_add_matrix = new_dataset.user_single_inter_matrix(form='coo').astype(np.float32)
    new_job_add_matrix = new_dataset.item_single_inter_matrix(form='coo').astype(np.float32)

    # 合并现有的交互矩阵和增量数据的交互矩阵
    combined_interaction_data = np.concatenate([existing_interaction_matrix.data, new_interaction_matrix.data])
    combined_interaction_row = np.concatenate([existing_interaction_matrix.row, new_interaction_matrix.row])
    combined_interaction_col = np.concatenate([existing_interaction_matrix.col, new_interaction_matrix.col])
    updated_interaction_matrix = coo_matrix((combined_interaction_data, (combined_interaction_row, combined_interaction_col)), shape=existing_interaction_matrix.shape)

    # 合并现有的用户单向交互矩阵和增量数据的用户单向交互矩阵
    combined_user_add_data = np.concatenate([existing_user_add_matrix.data, new_user_add_matrix.data])
    combined_user_add_row = np.concatenate([existing_user_add_matrix.row, new_user_add_matrix.row])
    combined_user_add_col = np.concatenate([existing_user_add_matrix.col, new_user_add_matrix.col])
    updated_user_add_matrix = coo_matrix((combined_user_add_data, (combined_user_add_row, combined_user_add_col)), shape=existing_user_add_matrix.shape)

    # 合并现有的项目单向交互矩阵和增量数据的项目单向交互矩阵
    combined_job_add_data = np.concatenate([existing_job_add_matrix.data, new_job_add_matrix.data])
    combined_job_add_row = np.concatenate([existing_job_add_matrix.row, new_job_add_matrix.row])
    combined_job_add_col = np.concatenate([existing_job_add_matrix.col, new_job_add_matrix.col])
    updated_job_add_matrix = coo_matrix((combined_job_add_data, (combined_job_add_row, combined_job_add_col)), shape=existing_job_add_matrix.shape)

    # 更新模型的交互矩阵
    model.interaction_matrix = updated_interaction_matrix
    model.user_add_matrix = updated_user_add_matrix
    model.job_add_matrix = updated_job_add_matrix

    # 重新计算邻接矩阵并更新模型
    model.edge_index, model.edge_weight = model.get_norm_adj_mat()
    model.edge_index = model.edge_index.to(model.device)
    model.edge_weight = model.edge_weight.to(model.device)

'''更新BERT嵌入数据'''
def update_bert_embeddings(model, new_dataset):
    # 获取现有的 BERT 嵌入
    # old_bert_user = model.bert_user
    old_bert_item = model.bert_item

    # print("old_bert_user.shape:", old_bert_user.shape)
    print("old_bert_item.shape:", old_bert_item.shape)

    # 获取新的 BERT 嵌入
    # new_bert_user = new_dataset.bert_user.to(config['device'])
    new_bert_item = new_dataset.bert_item.to(config['device'])
    # 去除第一行的空值
    new_bert_item = new_bert_item[1:] if new_bert_item[0].sum() == 0 else new_bert_item
    print("new_bert_item.shape:", new_bert_item.shape)

    # 合并现有的 BERT 嵌入和增量数据的 BERT 嵌入
    # updated_bert_user = torch.cat([old_bert_user, new_bert_user], dim=0)
    updated_bert_item = torch.cat([old_bert_item, new_bert_item], dim=0)
    print("updated_bert_item.shape:", updated_bert_item.shape)

    # 更新模型的 BERT 嵌入
    # model.bert_user = updated_bert_user
    model.bert_item = updated_bert_item

print("=====1、读取配置文件=====")
config = PJFConfig(model='DPGNN', dataset='zhilian', config_file_list=None, config_dict=None)

init_seed(config['seed'], config['reproducibility'])

# 判断设备类型
config['device'] = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print("=====2、加载已训练好的模型=====")
trained_model_path = './saved/DPGNN-Sep-10-2024_23-29-08.pth'
model, valid_data = load_trained_model(config, trained_model_path)

print("=====3、处理新增加的训练数据=====")
new_config = PJFConfig(model='DPGNN', dataset='zhilian_Increment', config_file_list=None, config_dict=None)
new_dataset = PJFDataset(new_config)

# 修改数据集划分比例
new_ratios = [1, 0, 0]
new_config['eval_args']['split']['RS'] = new_ratios

# 创建加载器
new_train_data, new_valid_data,  new_test_data= data_preparation(new_config, new_dataset)

print("=====4、基于增量数据更新模型参数=====")
print("==4.1 更新交互矩阵==")
# 更新交互矩阵
update_interaction_matrices(model, new_dataset)

print("==4.2 更新BERT嵌入==")
# 更新 BERT 嵌入
update_bert_embeddings(model, new_dataset)

print("==4.3 初始化新用户和新项目的嵌入==")
# 初始化新用户和新项目的嵌入
# num_new_users = len(new_dataset.user_list)  # 假设你有新的用户数量
num_new_users = 0  # 假设你有新的用户数量
num_new_items = 7  # 假设你有新的项目数量
initialize_new_embeddings(model, num_new_users, num_new_items)

print("=====5、加载训练器=====")
trainer = get_trainer(config['MODEL_TYPE'], config['model'],
                          multi_direction=config['biliteral'])(config, model)

config['checkpoint_dir'] = 'Incremental_saved'
print("=====6、开始增量训练=====")
best_valid_score, best_valid_result = trainer.fit(
    new_train_data, valid_data, saved=True, show_progress=config['show_progress']
)

print("=====7、增量训练结束=====")
print("best_valid_score:", best_valid_score)
print("valid_score_bigger:", config['valid_metric_bigger'])
print("best_valid_result:", best_valid_result)






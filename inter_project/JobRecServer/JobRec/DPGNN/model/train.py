import os

import torch
import yaml
from JobRec.DPGNN.model.dpgnn import DPGNN
import pandas as pd
from JobRec.DPGNN.Utils.config import PJFConfig
from JobRec.DPGNN.Dataset.dataset import *
from JobRec.DPGNN.Dataset.utils import data_preparation, create_dataset
from recbole.utils import init_logger, init_seed, set_color
from JobRec.DPGNN.Utils.utils import get_trainer, get_model

import os


os.environ['CURL_CA_BUNDLE'] = ''
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
os.environ['ALL_PROXY'] = "socks5://127.0.0.1:7897"

print("=====1、读取配置文件=====")
config = PJFConfig(model='DPGNN', dataset='xdu', config_file_list=None, config_dict=None)
# print(config)

init_seed(config['seed'], config['reproducibility'])

# 判断设备类型
config['device'] = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('device:', config['device'])

print("=====2、数据集处理=====")
dataset = create_dataset(config)

train_data, valid_data, test_data = data_preparation(config, dataset)

print("=====3、初始化模型实例=====")
model = get_model(config['model'])(config, train_data.dataset).to(config['device'])
# model = DPGNN(config, train_data.dataset).to(config['device'])

print("=====4、加载训练器=====")
# <class 'JobRec.DPGNN.Utils.trainer.MultiDirectTrainer'>
trainer = get_trainer(config['MODEL_TYPE'], config['model'],
                          multi_direction=config['biliteral'])(config, model)


print("=====5、开始训练=====")
best_valid_score, best_valid_result = trainer.fit(
    train_data, valid_data, saved=True, show_progress=config['show_progress']
)

print("=====6、验证结束=====")
print("best_valid_score:",best_valid_score)
print("valid_score_bigger:",config['valid_metric_bigger'])
print("best_valid_result:",best_valid_result)

# print("=====4、开始Test=====")
# trainer.predictTest(test_data, load_best_model=True,
#                     model_file='./saved/DPGNN-Jun-19-2024_11-51-39.pth',
#                     show_progress=config['show_progress'])

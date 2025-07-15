import os

import torch
import re
from JobRec.DPGNN.model.dpgnn import DPGNN
import pandas as pd
from JobRec.DPGNN.Utils.config import PJFConfig
from JobRec.DPGNN.Dataset.dataset import PJFDataset
from JobRec.DPGNN.Dataset.utils import data_preparation
from recbole.utils import init_logger, init_seed, set_color
from JobRec.DPGNN.Utils.utils import get_trainer, get_model
from datetime import datetime

def test_model():
    print("=====1、读取配置文件=====")
    config = PJFConfig(model='DPGNN', dataset='xdu', config_file_list=None, config_dict=None)
    # print(config)

    init_seed(config['seed'], config['reproducibility'])

    # 判断设备类型
    config['device'] = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    print("=====2、数据集处理=====")
    dataset = PJFDataset(config)
    # 修改数据集划分比例
    # new_ratios = [0.8, 0.2, 0]
    # config['eval_args']['split']['RS'] = new_ratios
    # print(dataset)

    train_data, valid_data, test_data = data_preparation(config, dataset)

    print("=====3、初始化模型实例=====")
    model = get_model(config['model'])(config, train_data.dataset).to(config['device'])
    # model = DPGNN(config, train_data.dataset).to(config['device'])
    print('device', config['device'])

    print("=====4、加载训练器=====")
    # <class 'JobRec.DPGNN.Utils.trainer.MultiDirectTrainer'>
    trainer = get_trainer(config['MODEL_TYPE'], config['model'],
                              multi_direction=config['biliteral'])(config, model)

    def get_latest_file(folder_path):
        # 正则表达式匹配文件名格式
        # pattern = r'BPJFNN-(\w{3})-(\d{2})-(\d{4})_(\d{2})-(\d{2})-(\d{2})\.pth'
        pattern = r'(?:\w+)-(\w{3})-(\d{2})-(\d{4})_(\d{2})-(\d{2})-(\d{2})\.pth'

        latest_file = None
        latest_time = datetime.min

        for filename in os.listdir(folder_path):
            match = re.match(pattern, filename)
            if match:
                # 解析文件名中的日期和时间
                month, day, year, hour, minute, second = match.groups()
                file_time = datetime.strptime(f"{month} {day} {year} {hour}:{minute}:{second}", "%b %d %Y %H:%M:%S")

                # 更新最新文件
                if file_time > latest_time:
                    latest_time = file_time
                    latest_file = filename

        if latest_file:
            return os.path.join(folder_path, latest_file)
        else:
            return None

    folder_path = r"G:\JobRecProject_v2\JobRec\DPGNN\model\saved"
    latest_file = get_latest_file(folder_path)
    #latest_file = r"G:\JobRecProject_v2\JobRec\DPGNN\model\saved\APJFNN-Aug-09-2024_18-01-06.pth"
    print(latest_file)

    print("=====5、开始Test=====")
    test_result = trainer.evaluate(test_data, load_best_model=True,
                        model_file=latest_file,
                        show_progress=config['show_progress'])

    print("=====6、测试结束=====")
    return test_result


if __name__ == "__main__":
    test_result = test_model()
    print("test_result:", test_result)
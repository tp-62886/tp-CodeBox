import torch
import numpy as np
from JobRecServer.JobRec.DPGNN.model.dpgnn import DPGNN
from JobRecServer.JobRec.DPGNN.Utils.config import PJFConfig
from JobRecServer.JobRec.DPGNN.Dataset.dataset import PJFDataset
from JobRecServer.JobRec.DPGNN.Dataset.utils import data_preparation
from recbole.utils import init_logger, init_seed, set_color

class JobRecommender:
    def __init__(self, config_file='zhilian', checkpoint_path='./saved/DPGNN-Jun-26-2024_01-56-07.pth'):
        '''1、读取配置文件'''
        print("=====1、读取配置文件=====")
        self.config = PJFConfig(model='DPGNN', dataset=config_file, config_file_list=None, config_dict=None)
        init_seed(self.config['seed'], self.config['reproducibility'])

        # 判断设备类型
        self.config['device'] = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        '''2、数据集处理'''
        print("=====2、数据集处理=====")
        self.dataset = PJFDataset(self.config)
        self.train_data, self.valid_data, self.test_data = data_preparation(self.config, self.dataset)
        self.num_samples = 1000

        # 收集并去重所有的 job_id、user_id
        self.all_job_ids = set()
        self.all_user_ids = set()
        for batch in self.train_data:
            self.all_job_ids.update(batch["job_id"].numpy())
            self.all_user_ids.update(batch["user_id"].numpy())
        self.all_job_ids = list(self.all_job_ids)
        self.all_user_ids = list(self.all_user_ids)
        self.num_samples = len(self.all_job_ids)
        self.user_num_samples = len(self.all_user_ids)

        '''3、创建模型实例'''
        print("=====3、创建模型实例=====")
        # 创建模型实例
        self.model = DPGNN(self.config, self.train_data.dataset).to(self.config['device'])

        print("=====3.1 开始加载模型权重=====")
        # 加载训练好的模型权重
        checkpoint = torch.load(checkpoint_path, map_location=self.config['device'])
        # print(checkpoint["state_dict"]['item_embedding_p.weight'].shape)
        # print(checkpoint["state_dict"]['item_embedding_p.weight'])
        # 使用 torch.load 加载模型检查点，并将状态字典和其他参数加载到模型中
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.load_other_parameter(checkpoint.get("other_parameter"))
        torch.no_grad()

        print("=====3.2 模型权重加载完成=====")

        # 确保模型与数据都在正确的设备上
        self.model = self.model.to(self.config['device'])
        self.model.eval()

    '''向候选人推荐工作'''
    def recommend_jobs_for_user(self, user_id_input, num_recommendations=10):
        '''4、开始预测'''
        print("=====4、开始预测=====")
        # 从所有的 job_id 中随机选取 num_samples 个
        random_job_ids = np.random.choice(self.all_job_ids, self.num_samples, replace=False)

        user_id_input = self.dataset.original_to_mapped['user_id'][user_id_input]

        # 构建 first_interaction 字典
        first_interaction = {
            self.config["USER_ID_FIELD"]: np.array([user_id_input] * self.num_samples),
            self.config["ITEM_ID_FIELD"]: random_job_ids
        }

        # 将数据转移到指定设备并转换为 tensor
        first_interaction = {key: torch.tensor(value).to(self.config['device']) for key, value in first_interaction.items()}

        # 进行预测
        origin_scores = self.model.predict(first_interaction)
        col_idx = first_interaction[self.config["ITEM_ID_FIELD"]]

        # 创建一个包含 (item_id, score) 的列表
        user_scores = [(col_idx[i].item(), origin_scores[i].item()) for i in range(self.num_samples)]
        # 根据评分对列表进行排序
        sorted_scores = sorted(user_scores, key=lambda x: x[1], reverse=True)

        recommendations = []
        for item_id, score in sorted_scores[:num_recommendations]:
            original_item_id = self.dataset.mapped_to_original['job_id'][item_id]
            recommendations.append((original_item_id, score))

        return recommendations

    '''向工作推荐候选人'''
    def recommend_users_for_job(self, job_id_input, num_recommendations=10):
        '''4、开始预测'''
        print("=====4、开始预测=====")
        # 从所有的 user_id 中随机选取 num_samples 个
        random_user_ids = np.random.choice(self.all_user_ids, self.user_num_samples, replace=False)
        # 将原始ID进行映射
        job_id_input = self.dataset.original_to_mapped['job_id'][job_id_input]

        # 构建 first_interaction 字典
        first_interaction = {
            self.config["USER_ID_FIELD"]: random_user_ids,
            self.config["ITEM_ID_FIELD"]: np.array([job_id_input] * self.user_num_samples)
        }

        # 将数据转移到指定设备并转换为 tensor
        first_interaction = {key: torch.tensor(value).to(self.config['device']) for key, value in first_interaction.items()}

        # 进行预测
        origin_scores = self.model.predict(first_interaction)
        col_idx = first_interaction[self.config["USER_ID_FIELD"]]

        # 创建一个包含 (user_id, score) 的列表
        user_scores = [(col_idx[i].item(), origin_scores[i].item()) for i in range(self.user_num_samples)]
        # 根据评分对列表进行排序
        sorted_scores = sorted(user_scores, key=lambda x: x[1], reverse=True)

        recommendations = []
        for user_id, score in sorted_scores[:num_recommendations]:
            original_item_id = self.dataset.mapped_to_original['user_id'][user_id]
            recommendations.append((original_item_id, score))

        return recommendations

# #示例调用
# recommender = JobRecommender(config_file='zhilian', checkpoint_path='./saved/DPGNN-Jun-19-2024_11-51-39.pth')
# user_id_input = 739  # 输入用户ID
# recommendations = recommender.recommend_jobs_for_user(user_id_input, num_recommendations=50)

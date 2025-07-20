# @Time   : 2022/3/4
# @Author : Chen Yang
# @Email  : flust@ruc.edu.cn

"""
recbole_pjf.trainer
########################
"""

from collections import OrderedDict

import torch
import pandas as pd
import json
import numpy as np
import pickle
from recbole.trainer import Trainer
from recbole.utils import calculate_valid_score


from recbole.data.interaction import Interaction
from JobRec.DPGNN.Dataset.dataloader import RFullSortEvalDataLoader, RNegSampleEvalDataLoader
from recbole.utils import (
    ensure_dir,
    get_local_time,
    early_stopping,
    calculate_valid_score,
    dict2str,
    EvaluatorType,
    KGDataLoaderState,
    get_tensorboard,
    set_color,
    get_gpu_usage,
    WandbLogger,
)
from tqdm import tqdm

class MultiDirectTrainer(Trainer):
    def __init__(self, config, model):
        super(MultiDirectTrainer, self).__init__(config, model)
        setattr(self.eval_collector.register,'rec.items', True)

    @torch.no_grad()
    def evaluate(self, eval_data, load_best_model=True, model_file=None, show_progress=False):
        # Overall look at the bilateral recommendation task

        if load_best_model:
            checkpoint_file = model_file or self.saved_model_file
            checkpoint = torch.load(checkpoint_file, map_location = self.device)
            self.model.load_state_dict(checkpoint["state_dict"])
            self.model.load_other_parameter(checkpoint.get("other_parameter"))
            message_output = "Loading model structure and parameters from {}".format(
                checkpoint_file
            )
            self.logger.info(message_output)
            
        self.model.eval()

        if isinstance(eval_data[0], RFullSortEvalDataLoader):
            eval_func = self._full_sort_batch_eval
            self.item_tensor = eval_data[0].dataset.get_item_feature().to(self.device)
        else:
            eval_func = self._neg_sample_batch_eval
        struct_g = self.collect_bilateral_info(eval_data[0], eval_func, show_progress, 1)
        test_result_g = self.evaluator.evaluate(struct_g)
        if not self.config["single_spec"]:
            test_result_g = self._map_reduce(test_result_g, num_sample)

        self.config.change_direction()
        if isinstance(eval_data[1], RFullSortEvalDataLoader):
            eval_func = self._full_sort_batch_eval
            self.item_tensor = eval_data[1].dataset.get_item_feature().to(self.device)
        else:
            eval_func = self._neg_sample_batch_eval
        struct_j = self.collect_bilateral_info(eval_data[1], eval_func, show_progress, 2)
        test_result_j = self.evaluator.evaluate(struct_j)
        if not self.config["single_spec"]:
            test_result_j = self._map_reduce(test_result_j, num_sample)
        self.config.change_direction()

        return test_result_g, test_result_j
    
    @torch.no_grad()
    def predictTest(self, eval_data, load_best_model=True, model_file=None, show_progress=False):
        # Overall look at the bilateral recommendation task

        # 加载最佳模型参数
        if load_best_model:
            # 确定要加载的模型文件路径，如果未提供 model_file，则使用已保存的模型文件路径 self.saved_model_file。
            checkpoint_file = model_file or self.saved_model_file
            checkpoint = torch.load(checkpoint_file, map_location=self.device)
            # 使用 torch.load 加载模型检查点，并将状态字典和其他参数加载到模型中
            self.model.load_state_dict(checkpoint["state_dict"])
            self.model.load_other_parameter(checkpoint.get("other_parameter"))
            message_output = "Loading model structure and parameters from {}".format(
                checkpoint_file  # "saved/DPGNN-May-28-2024_17-36-09.pth"
            )
            self.logger.info(message_output)

        # 设置模型为评估模式
        self.model.eval()

        if isinstance(eval_data[0], RFullSortEvalDataLoader):
            eval_func = self._full_sort_batch_eval
            self.item_tensor = eval_data[0].dataset.get_item_feature().to(self.device)
        else:
            eval_func = self._neg_sample_batch_eval
        struct_g = self.collect_bilateral_info(eval_data[0], eval_func, show_progress, 1)
        test_result_g = self.evaluator.evaluate(struct_g)

        # === 测试专用代码：查看预测后的结果 ===
        pos_idx = struct_g.get("rec.items")
        # pos_idx_topk = struct_g.get("rec.topk")
        # topk_idx, pos_len_list = torch.split(pos_idx_topk, [5, 1], dim=1)

        pos_idx_np = pos_idx.numpy()
        # pos_idx_np_topk = pos_idx_topk.numpy()
        # # 创建一个用户ID列
        user_ids = np.arange(pos_idx_np.shape[0])
        # user_ids_topk = np.arange(pos_idx_np.shape[0])

        # # 创建一个 DataFrame
        df = pd.DataFrame(pos_idx_np, columns=[f'Recommendation_{i+1}' for i in range(pos_idx_np.shape[1])])
        df.insert(0, 'User_ID', user_ids)

        # df_topk = pd.DataFrame(pos_idx_np_topk, columns=[f'Recommendation_{i+1}' for i in range(pos_idx_np_topk.shape[1])])
        # df_topk.insert(0, 'User_ID', user_ids_topk)

        # # 保存为 CSV 文件
        df.to_csv('/root/autodl-tmp/RecBole-PJF-main/cheakData/recommendations_geek_50.csv', index=False)
        # df_topk.to_csv('recommendations_geek_topk.csv', index=False)

        # print("Recommendations saved to recommendations_g.csv")

        self.config.change_direction()
        if isinstance(eval_data[1], RFullSortEvalDataLoader):
            eval_func = self._full_sort_batch_eval
            self.item_tensor = eval_data[1].dataset.get_item_feature().to(self.device)
        else:
            eval_func = self._neg_sample_batch_eval
        struct_j = self.collect_bilateral_info(eval_data[1], eval_func, show_progress, 2)

        pos_idx_j = struct_j.get("rec.items")
        pos_idx_j_np = pos_idx_j.numpy()

        # pos_idx_topk = struct_j.get("rec.topk")
        # topk_idx, pos_len_list = torch.split(pos_idx_topk, [5, 1], dim=1)
        # pos_idx_np_topk = pos_idx_topk.numpy()

        # 创建一个用户ID列
        job_ids = np.arange(pos_idx_j_np.shape[0])
        

        # 创建一个 DataFrame
        df_j = pd.DataFrame(pos_idx_j_np, columns=[f'Recommendation_{i+1}' for i in range(pos_idx_j_np.shape[1])])
        df_j.insert(0, 'Job_ID', job_ids)

        # df_topk = pd.DataFrame(pos_idx_np_topk, columns=[f'Recommendation_{i+1}' for i in range(pos_idx_np_topk.shape[1])])
        # df_topk.insert(0, 'Job_ID', job_ids)

        # 保存为 CSV 文件
        df_j.to_csv('/root/autodl-tmp/RecBole-PJF-main/cheakData/recommendations_job_50.csv', index=False)
        print("Recommendations saved to recommendations_j.csv")
        # df_topk.to_csv('recommendations_job_topk.csv', index=False)
        
        
    
    def _full_sort_batch_eval(self, batched_data):
        interaction, history_index, positive_u, positive_i = batched_data

        inter_len = len(interaction)
        new_inter = interaction.to(self.device).repeat_interleave(self.tot_item_num)
        batch_size = len(new_inter)
        new_inter.update(self.item_tensor.repeat(inter_len))
        if batch_size <= self.test_batch_size:
            scores = self.model.predict(new_inter)
        else:
            scores = self._spilt_predict(new_inter, batch_size)

        scores = scores.view(-1, self.tot_item_num)
        scores[:, 0] = -np.inf
        if history_index is not None:
            scores[history_index] = -np.inf
        return interaction, scores, positive_u, positive_i

    def collect_bilateral_info(self, eval_data, eval_func, show_progress, direct = 0):
        if self.config['eval_type'] == EvaluatorType.RANKING:
            self.tot_item_num = eval_data.dataset.item_num

        iter_data = (
            tqdm(
                eval_data,
                total=len(eval_data),
                ncols=100,
                desc=set_color(f"Evaluate   ", "pink"),
            )
            if show_progress
            else eval_data
        )

        positive_u_list = []

        num_sample = 0
        for batch_idx, batched_data in enumerate(iter_data):
            num_sample += len(batched_data)
            interaction, scores, positive_u, positive_i = eval_func(batched_data[:4])
            if self.gpu_available and show_progress:
                iter_data.set_postfix_str(
                    set_color("GPU RAM: " + get_gpu_usage(self.device), "yellow")
                )

            self.eval_collector.eval_batch_collect(
                scores, interaction, positive_u, positive_i
            )

        self.eval_collector.model_collect(self.model)
        struct = self.eval_collector.get_data_struct()
        return struct
        

    def _valid_epoch(self, valid_data, show_progress=False):
        valid_result_all = self.evaluate(valid_data, load_best_model=False, show_progress=show_progress)
        valid_g_score = calculate_valid_score(valid_result_all[0], self.valid_metric)
        valid_j_score = calculate_valid_score(valid_result_all[1], self.valid_metric)
        valid_score = (valid_g_score + valid_j_score) / 2

        valid_result = OrderedDict()
        valid_result['For geek'] = valid_result_all[0]
        valid_result['\nFor job'] = valid_result_all[1]
        return valid_score, valid_result

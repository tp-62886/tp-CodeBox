# @Time   : 2022/3/2
# @Author : Chen Yang
# @Email  : flust@ruc.edu.cn

"""
recbole_pjf.utils
########################
"""

import importlib
from recbole.utils import get_model as get_recbole_model
from recbole.utils import get_trainer as get_recbole_trainer
'''
根据模型名称动态选择并返回相应的模型类
'''
def get_model(model_name):
    r"""Automatically select model class based on model name

    Args:
        model_name (str): model name

    Returns:
        Recommender: model class
    """
    model_file_name = model_name.lower()
    model_module = None
    # 生成模块路径，例如 'recbole_pjf.model.dpgnn'
    module_path = '.'.join(['JobRec.DPGNN.model', model_file_name])
    if importlib.util.find_spec(module_path, __name__):
        model_module = importlib.import_module(module_path, __name__)

    if model_module is None:
        return get_recbole_model(model_name)
    # 从导入的模块中获取模型类
    model_class = getattr(model_module, model_name)
    return model_class


def get_trainer(model_type, model_name, multi_direction=False):
    r"""Automatically select trainer class based on model type and model name

    Args:
        model_type (ModelType): model type
        model_name (str): model name
        multi_direction (bool): is evaluate in two directions

    Returns:
        Trainer: trainer class
    """
    try:
        # 导入 recbole_pjf.trainer 模块。
        # 获取以 model_name 为前缀的训练器类（例如'DPGNNTrainer' 类）
        return getattr(importlib.import_module('JobRec.DPGNN.Utils.trainer'), model_name + 'Trainer')
    except AttributeError:
        if multi_direction:
            # 开启双向评估，导入 MultiDirectTrainer类
            return getattr(importlib.import_module('JobRec.DPGNN.Utils.trainer'), 'MultiDirectTrainer')
        else:
            return get_recbole_trainer(model_type, model_name)

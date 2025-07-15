import runpy

# 增量训练
runpy.run_path('DPGNN\model\Incremental_training_xdu.py')

# 合并数据集
runpy.run_path('dataset\merge_dataset_xdu.py')

# 重新训练模型
runpy.run_path(r'DPGNN\model\train.py')

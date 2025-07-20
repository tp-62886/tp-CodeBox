import torch

class Interaction:
    def __init__(self, data):
        self.interaction = data

# 示例数据
data = {
    'user_id': torch.tensor([1, 2, 3]),
    'item_id': torch.tensor([101, 102, 103]),
    'label': torch.tensor([1.0, 0.0, 1.0])
}

# 创建 Interaction 对象
interaction = Interaction(data)

# 提取 interaction 对象中每个特征的第一条数据
first_data = {key: value[0].item() for key, value in interaction.interaction.items()}

print("=====First data=====")
print(first_data)

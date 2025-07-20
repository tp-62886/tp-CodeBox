import torch
import time

# 检查 CUDA 是否可用
if torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
else:
    device = torch.device("cpu")
    print("CUDA is not available. Using CPU.")

# 创建大矩阵
size = 10000
a = torch.randn(size, size, device=device)
b = torch.randn(size, size, device=device)

# 持续进行矩阵乘法计算
print("Starting continuous matrix multiplication...")
while True:
    result = torch.mm(a, b)
    # 打印结果的摘要以防止优化器忽略计算
    print(f"Result sum: {result.sum().item()}")
    # 可选的延时，防止输出过多占用CPU资源
    time.sleep(1)

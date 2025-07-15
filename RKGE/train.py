from RKGE.data_process_com import data_process_job
from RKGE.data_process_xdu import data_process_student
from RKGE.recurrent_neural_network_xdu import train_student_model
from RKGE.recurrent_neural_network_com import train_job_model


def train():
    print("开始训练冷启动模型")
    # 学生数据处理
    # data_process_student()

    # 模型训练
    # train_student_model()

    # 职位数据处理
    # data_process_job()

    # 模型训练
    # train_job_model()


if __name__ == '__main__':
    train()

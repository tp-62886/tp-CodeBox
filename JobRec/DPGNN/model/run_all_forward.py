import sys
import os
import runpy
import csv
from JobRec.dataset.xdu.prepare_xdu import zhilian
from JobRec.DPGNN.model.model_test import test_model

def run_script(script_path):
    print(f"执行脚本: {script_path}")
    try:
        runpy.run_path(script_path)
    except Exception as e:
        print(f"执行 {script_path} 时出错: {e}")
        raise

def delete_files():
    # 定义要删除文件的路径
    dataset_path = r'G:\JobRecProject_v2\JobRec\dataset\xdu'
    saved_model_path = r'G:\JobRecProject_v2\JobRec\DPGNN\model\saved'

    # 删除dataset_path下除了.py外的所有文件
    for filename in os.listdir(dataset_path):
        file_path = os.path.join(dataset_path, filename)
        if os.path.isfile(file_path) and not filename.endswith('.py'):
            print(f"删除文件: {file_path}")
            os.remove(file_path)

    # 删除saved_model_path下的所有文件
    for filename in os.listdir(saved_model_path):
        file_path = os.path.join(saved_model_path, filename)
        if os.path.isfile(file_path):
            print(f"删除文件: {file_path}")
            os.remove(file_path)

def main():
    # 定义脚本路径
    train_path = r'G:\JobRecProject_v2\JobRec\DPGNN\model\train.py'

    # 添加脚本所在目录到 Python 路径
    sys.path.append(os.path.dirname(train_path))

    # 基准字段
    u_columns = ['DEPARTMENT', 'MAJOR', 'ZYFX', 'XBMC', 'ZXWYYZMC', 'XLMC', 'XXXSMC', 'JTDZ', 'GZZWLBMC']

    # 候选字段
    candidate_columns = ['6_LWMC']

    # 保存结果的列表
    results = []

    try:
        # 执行 prepare_xdu.py
        zhilian(u_columns)

        # 执行 train.py
        run_script(train_path)

        # 执行 model_test.py
        test_result = test_model()
        best_result = test_result[0]["recall@5"]
        print("Initial test_result:", best_result)
        delete_files()

        # 记录初始结果
        results.append({
            "iteration": 0,
            "current_column": "Initial",
            "all_columns": ', '.join(u_columns),
            "columns_count": len(u_columns),
            "current_result": best_result,
            "best_result": best_result
        })

        # 逐个添加候选字段进行测试
        for i, column in enumerate(candidate_columns):
            print(f"尝试添加字段: {column}")
            new_columns = u_columns + [column]

            # 重新执行 prepare_xdu.py
            zhilian(new_columns)

            # 重新执行 train.py
            run_script(train_path)

            # 重新执行 model_test.py 并获取测试结果
            test_result = test_model()
            current_result = test_result[0]["recall@5"]
            print(f"Result after adding {column}:", current_result)
            delete_files()

            # 判断是否保留新增字段
            if current_result >= best_result:
                print(f"保留字段: {column}")
                u_columns.append(column)
                best_result = current_result
            else:
                print(f"去除字段: {column}")

            # 记录当前结果
            results.append({
                "iteration": i + 1,
                "current_column": column,
                "all_columns": ', '.join(u_columns),
                "columns_count": len(u_columns),
                "current_result": current_result,
                "best_result": best_result
            })

        # 保存结果到 CSV 文件
        csv_file = 'field_selection_results_2.csv'
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=["iteration", "current_column", "all_columns", "columns_count", "current_result", "best_result"])
            writer.writeheader()
            writer.writerows(results)

    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

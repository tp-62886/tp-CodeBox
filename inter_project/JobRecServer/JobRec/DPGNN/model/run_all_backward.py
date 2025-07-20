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
    dataset_path = r'G:\JobRecProject_v2\JobRec\dataset\xdu'
    saved_model_path = r'G:\JobRecProject_v2\JobRec\DPGNN\model\saved'

    for filename in os.listdir(dataset_path):
        file_path = os.path.join(dataset_path, filename)
        if os.path.isfile(file_path) and not (filename.endswith('.py') or filename.endswith('.ivec') or filename.endswith('.uvec')):
            print(f"删除文件: {file_path}")
            os.remove(file_path)

    for filename in os.listdir(saved_model_path):
        file_path = os.path.join(saved_model_path, filename)
        if os.path.isfile(file_path):
            print(f"删除文件: {file_path}")
            os.remove(file_path)


def save_results(results, csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["iteration", "removed_column", "all_columns", "columns_count",
                                                  "current_result", "best_result"])
        writer.writeheader()
        writer.writerows(results)


def load_results(csv_file):
    u_columns = ['SID', 'GRADE', '34_KYLCG_QTKYCG', 'BIRTHDAY', '34_QTRCXX_DYSWSC',
                 '9_GGPA', '33_PJBJPM', '33_PJCJ', '33_PJNJPM', '34_QTRCXX_DYCXMCS',
                 '18_total_nourish', '34_KYLCG_ZZ', '30_total_deed', '34_QTRCXX_MRSWSC', '10_total_journals',
                 '34_FKYLCG_SXSJYYJSHD', '7_SFTG', '26_GJPYLX', '6_total_papers', '7_KSXMDM',
                 '7_total_level46', '31_total_project', '29_total_test',
                 '21_total_otherAchievement', '34_KYLCG_KYXM', '34_GJHPYCG_GJHY', '32_BRSFZYWCR',
                 '20_total_paper2', '2_UGGPA', '34_JCQK_GRXJSJJBD', '12_total_books', '34_KYLCG_ZL',
                 '13_total_patents', '11_total_conference', '16_total_paperAward', '5_total_ugscholarship',
                 '17_total_hlConference', '22_total_patent', '5_JXJDM', '27_total_practice', '34_JCQK_HJYRYCH',
                 '34_FKYLCG_JNRZ', '10_TYCS', '34_FKYLCG_QTFKYCG', '4_total_gscholarship', '34_KYLCG_LW',
                 '28_total_skill', '34_GJHPYCG_GJXM', '15_total_activity', '24_ZZBRJS', '24_total_book2',
                 '26_total_nourish2', '24_YZ', '5_JXJDJDM', '10_YXYZ', '25_total_iconference', '34_KCXX_YXKCSL',
                 '23_total_volunteer', '32_total_nresearch', '34_XSGZYJZGW_YJSJRFDY', '34_KCXX_YXKCXF',
                 '23_FWSC(H)', '12_BRZXZS', '34_KCXX_XWKPJF', '14_total_awards', '34_XSGZYJZGW_ZY',
                 '36_KQYNL', '36_GTBD', '34_QTRCXX_YKTYE', '20_GXD', '34_QTRCXX_DYJRTSGCS', '20_YXYZ',
                 '36_TDHZ', '36_ZHNL', '34_JZXX_ZYJT', '36_KJNL', '36_XSJL', '36_ZZGL', '36_YJNL',
                 '36_WYSP', '36_XSZYNL', '36_SJNL', '36_ZSJC', '36_GJSY', '34_QTRCXX_DYYKTXFCS',
                 '34_XSGZYJZGW_ZG', '31_XMJF', '34_FKYLCG_ZYFW', '7_CJ', '4_JXJJE', '34_JZXX_QTBZ',
                 '24_GRZXZS', '5_JE']
    if not os.path.exists(csv_file):
        return [], 0, u_columns

    results = []
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            results.append(row)

    if results:
        last_result = results[-1]
        iteration = int(last_result["iteration"])
        all_columns = last_result["all_columns"].split(", ")
        return results, iteration, all_columns
    else:
        return [], 0, []


def main():
    train_path = r'G:\JobRecProject_v2\JobRec\DPGNN\model\train.py'
    sys.path.append(os.path.dirname(train_path))

    csv_file = 'field_selection_results_v2.csv'
    results, iteration, all_columns = load_results(csv_file)

    # 保存结果的列表
    best_result = results[-1]["best_result"] if results else None

    try:
        if iteration == 0:
            zhilian(all_columns)
            run_script(train_path)
            test_result = test_model()
            best_result = test_result[0]["recall@5"]
            print("Initial test_result:", best_result)
            delete_files()

            results.append({
                "iteration": 0,
                "removed_column": "None",
                "all_columns": ', '.join(all_columns),
                "columns_count": len(all_columns),
                "current_result": best_result,
                "best_result": best_result
            })
            save_results(results, csv_file)
            iteration += 1

        for i in range(len(all_columns) - iteration, 0, -1):
            column_to_remove = all_columns[i]
            print(f"尝试删除字段: {all_columns[i]}")
            new_columns = all_columns[:i] + all_columns[i + 1:]

            zhilian(new_columns)
            run_script(train_path)
            test_result = test_model()
            current_result = test_result[0]["recall@5"]
            print(f"Result after removing {all_columns[i]}:", current_result)
            delete_files()

            if current_result >= float(best_result):
                print(f"删除字段: {all_columns[i]}")
                all_columns = new_columns
                best_result = current_result
            else:
                print(f"保留字段: {all_columns[i]}")

            results.append({
                "iteration": len(all_columns) - i,
                "removed_column": column_to_remove,
                "all_columns": ', '.join(all_columns),
                "columns_count": len(all_columns),
                "current_result": current_result,
                "best_result": best_result
            })
            save_results(results, csv_file)
            iteration += 1

    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

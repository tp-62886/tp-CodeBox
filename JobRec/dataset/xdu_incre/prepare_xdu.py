# @Time   : 2022/4/10
# @Author : Chen Yang
# @Email  : flust@ruc.edu.cn

"""
data_round1
"""

import jieba
import re
import csv

class zhilian:
    def __init__(self, u_columns):
        print('hello')
        self.get_inter()
        self.get_user_item(u_columns)
        self.get_docs()
        pass

    def get_inter(self):
        f = open(r'G:\西电就业数据集\训练数据集\csv\incre\xdu_dataset_action_incre.csv', 'r', encoding='utf-8')
        f_target = open(r'G:\JobRecProject_v2\JobRec\dataset\xdu_incre\xdu.inter', 'w', encoding='utf-8')
        f.readline()
        f_target.write('user_id:token\tjob_id:token\tdirect:token\tlabel:float\n')
        self.uid_set = set()
        self.jid_set = set()
        line_count = 0
        for line in f:
            uid, jid, s = line[:-1].split(',')
            # if b == '0' and d == '0' and s == '0':
            if s == '0':
                continue
            self.uid_set.add(uid)
            self.jid_set.add(jid)
            import random
            if random.random() < 0.5:
                direct = '0'
            else:
                direct = '1'
            new_line = '\t'.join([uid, jid, direct, s]) + '\n'
            f_target.write(new_line)
            line_count += 1
        print("uid count is: ", len(self.uid_set))
        print("jid count is: ", len(self.jid_set))
        print("line count is: ", line_count)

    def get_user_item(self, u_columns):
        # 指定要提取的用户数据的字段名
        # u_columns = ['SID', '18_total_nourish', '7_SFTG', '2_UGGPA', '34_QTRCXX_DYCXMCS', '34_FKYLCG_SXSJYYJSHD',
        #              '34_GJHPYCG_GJHY', '34_FKYLCG_QTFKYCG', '3_total_honor', '17_total_hlConference',
        #              '34_KYLCG_QTKYCG', '7_total_level46', '3_RYCHDM', '30_total_deed', '31_total_project',
        #              '34_QTRCXX_DYSWSC', '26_GJPYLX', '26_total_nourish2', '33_PJNJPM', '5_JXJDJDM',
        #              '34_GJHPYCG_GJXM', '7_KSXMDM', '33_PJBJPM', '32_BRSFZYWCR', '4_total_gscholarship',
        #              '34_QTRCXX_MRSWSC', '16_total_paperAward', '21_total_otherAchievement', '12_total_books',
        #              '34_KYLCG_ZZ', '33_PJCJ', '24_total_book2', '32_total_nresearch', '5_total_ugscholarship',
        #              '34_JCQK_GRXJSJJBD', '14_total_awards', '5_JXJDM', '25_total_iconference', '34_FKYLCG_JNRZ',
        #              '12_BRZXZS', '27_total_practice', '34_KYLCG_ZL', '34_KYLCG_LW',
        #              '34_KYLCG_KYXM', '24_YZ', '34_XSGZYJZGW_YJSJRFDY', '29_WYLX',
        #              '24_ZZBRJS', '11_total_conference', '20_total_paper2']

        # 打开原始CSV文件和新文件
        with open(r'G:\西电就业数据集\训练数据集\csv\xdu_dataset_user.csv', 'r',
                  encoding='utf-8') as f:
            with open(r'G:\JobRecProject_v2\JobRec\dataset\xdu_incre\xdu.user', 'w', encoding='utf-8', newline='') as f_user:
                reader = csv.reader(f)
                writer = csv.writer(f_user, delimiter='\t')

                # 读取并处理表头
                head = next(reader)
                col_indices = [head.index(col) for col in u_columns]  # 获取指定字段名的索引
                selected_head = [head[i] for i in col_indices]
                selected_head = [i + ':token' for i in selected_head]
                writer.writerow(selected_head)

                user_line_count = 0
                # 遍历每一行用户数据
                for line in reader:
                    lines = [line[i] for i in col_indices]

                    if lines[0] in self.uid_set:
                        writer.writerow(lines)
                        user_line_count += 1
                print("user line count:", user_line_count)

        # 指定要提取的工作数据的字段名
        j_columns = ['DWZZJGDM', '37_avg_SYQ', '37_avg_WYJ', '37_avg_SYQX', '37_avg_ZZQX', '37_QYLX',
                     '39_DWGM', '39_DWLB']

        # 打开工作数据文件进行读取
        with open(r'G:\西电就业数据集\训练数据集\csv\xdu_dataset_job.csv', 'r', encoding='utf-8') as f:
            with open(r'G:\JobRecProject_v2\JobRec\dataset\xdu_incre\xdu.item', 'w', encoding='utf-8', newline='') as f_item:
                reader = csv.reader(f)
                writer = csv.writer(f_item, delimiter='\t')

                # 读取并处理表头
                head = next(reader)
                col_indices = [head.index(col) for col in j_columns]  # 获取指定字段名的索引
                selected_head = [head[i] for i in col_indices]
                selected_head[0] = 'job_id'
                selected_head = [i + ':token' for i in selected_head]
                writer.writerow(selected_head)

                job_line_count = 0
                # 遍历每一行工作数据
                for line in reader:
                    lines = [line[i] for i in col_indices]
                    if lines[0] in self.jid_set:
                        writer.writerow(lines)
                        job_line_count += 1
                print("job line count:", job_line_count)

    def get_docs(self):
        # 指定要提取的用户数据的字段名
        u_columns = [
            "DEPARTMENT", "MAJOR", "ZYFX", "XBMC", "ZXWYYZMC", "XLMC", "XXXSMC", "JTDZ", "GZZWLBMC", "6_LWMC",
            "6_FBKW", "10_PIM", "10_QKMC", "10_JSLB", "10_JCRFQ", "10_PM", "11_PIM", "11_HYMC", "11_HYLB", "11_PM",
            "12_ZZMC", "12_PM", "13_ZLTM", "13_SQLX", "13_ZLWXZL", "14_JXMC", "14_FJJG", "15_HDMC", "15_HDFS",
            "15_ZZDW", "15_BRJS", "15_HDQDCG", "16_JXMC", "16_CGLB", "16_CGMC", "16_JXJB", "17_HYZT", "17_BRJS",
            "17_ZBDW", "18_YJFX", "20_FQ", "20_HYMC", "21_CGMC", "21_CGCXD", "21_CGCNYYZHQK", "22_ZLMC", "22_ZLJJ",
            "22_ZLZHQK", "24_BRSZGZ", "25_HYMC", "25_HYZT", "26_XMMC", "26_YJFX", "27_HDMC", "30_BDMC", "31_XMMC",
            "31_XMLY", "31_ZZWCDW", "34_XSGZYJZGW_XSGBJL"]

        with open(r'G:\西电就业数据集\训练数据集\csv\xdu_dataset_user.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            with open(r'G:\JobRecProject_v2\JobRec\dataset\xdu_incre\xdu.udoc', 'w', encoding='utf-8', newline='') as f_udoc:
                writer = csv.writer(f_udoc, delimiter='\t')
                head = ['user_id:token', 'user_doc:token_seq']
                writer.writerow(head)
                user_doc_line_count = 0
                for row in reader:
                    if row['SID'] not in self.uid_set:
                        continue
                    user_doc_line_count += 1
                    for col in u_columns:  # Skip 'SID' because it is used as the key
                        if row[col] and row[col] != '-':
                            sents = row[col]
                            try:
                                sent_wds, sent_lens, _ = raw2token_seq(sents)
                                sent_wds = sent_wds.split(' ')
                                sent_lens = sent_lens.split(' ')
                                a = -(int)(sent_lens[-1])
                                for j in range(len(sent_lens)):
                                    a += int(sent_lens[j - 1])
                                    s_word_line = ' '.join(sent_wds[a:a + int(sent_lens[j])])
                                    s_new_line = row['SID'] + '\t' + s_word_line + '\n'
                                    f_udoc.write(s_new_line)
                            except:
                                print(sents)
                                f_udoc.write(row['SID'] + '\t' + sents + '\n')
                print("user_doc_line_count:", user_doc_line_count)

        # 指定要提取的工作数据的字段名
        j_columns = ['SJDWMC', 'DWXZMC', 'DWHYMC', 'DWSZDDM', '39_DWBQ']

        with open(r'G:\西电就业数据集\训练数据集\csv\xdu_dataset_job.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            with open(r'G:\JobRecProject_v2\JobRec\dataset\xdu_incre\xdu.idoc', 'w', encoding='utf-8', newline='') as f_idoc:
                writer = csv.writer(f_idoc, delimiter='\t')
                head = ['job_id:token', 'job_doc:token_seq']
                writer.writerow(head)
                job_doc_line_count = 0
                for row in reader:
                    if row['DWZZJGDM'] not in self.jid_set:
                        continue
                    job_doc_line_count += 1
                    for col in j_columns:  # Skip 'DWZZJGDM' because it is used as the key
                        if row[col] and row[col] != '-' and row[col] != '\\N':
                            sents = row[col]
                            try:
                                sent_wds, sent_lens, _ = raw2token_seq(sents)
                                sent_wds = sent_wds.split(' ')
                                sent_lens = sent_lens.split(' ')
                                a = -(int)(sent_lens[-1])
                                for i in range(len(sent_lens)):
                                    a += int(sent_lens[i - 1])
                                    s_word_line = ' '.join(sent_wds[a:a + int(sent_lens[i])])
                                    s_new_line = row['DWZZJGDM'] + '\t' + s_word_line + '\n'
                                    f_idoc.write(s_new_line)
                            except:
                                print(sents)
                                f_idoc.write(row['DWZZJGDM'] + '\t' + sents + '\n')
                print("job doc line count:", job_doc_line_count)

# jieba.load_userdict(os.path.join(r'./origin_data_1/job_word.dct'))  # 加载自定义字典
# jobwd2jobtag = {}
# with open(os.path.join(r'./origin_data_1/basic-tag-data-online-v14.json'), 'r', encoding='utf-8') as file:
#     for line in file:
#         js = json.loads(line.strip())
#         jobtag = js['tag_word']
#         for wd in js['writing_words']:
#             jobwd2jobtag[wd] = jobtag


def clean_text(text):
    illegal_set = ',.;?!~[]\'"@#$%^&*()-_=+{}\\`～·！¥（）—「」【】|、“”《<》>？，。…：'   # 定义非法字符

    for c in illegal_set:
        text = text.replace(c, ' ')     # 非法字符 替换为 空格
    for pattern in ['岗位职责', '职位描述', '工作内容', '岗位描述', '岗位说明', '工作职责', '你的职责']:
        text = text.replace(pattern, '')   # 内容头部替换为空格
    text = ' '.join([_ for _ in text.split(' ') if len(_) > 0])
    return text    # 空格间隔


def cut_sent(text):
    wds = [_.strip() for _ in jieba.cut(text) if len(_.strip()) > 0]  # 分词，返回分词后的 list
    return wds


def split_sent(text):
    text = re.split('(?:[0-9][.;。：．•）\)])', text)  # 按照数字分割包括  1.  1;  1。  1：  1) 等
    ans = []
    for t in text:
        for tt in re.split('(?:[\ ][0-9][、，])', t):  #
            for ttt in re.split('(?:^1[、，])', tt):   # 1、
                for tttt in re.split('(?:\([0-9]\))', ttt):   # (1)
                    ans += re.split('(?:[。；…●])', tttt)

    return [_.strip() for _ in ans if len(_.strip()) > 0]


def raw2token_seq(s):
    sents = split_sent(s)
    sent_wds = []
    sent_lens = []
    for sent in sents:
        # 对于分段后每段文字：
        if len(sent) < 2:
            continue
        sent = clean_text(sent)
        if len(sent) < 1:
            continue
        wds = cut_sent(sent)
        # 切词
        # for wd in wds:
        #     if wd in jobwd2jobtag:
        #         wd = jobwd2jobtag[wd]
        #     # 词 对应的 tag
        # if len(wds) < 1: continue
        sent_wds.extend(wds)
        sent_lens.append(len(wds))
    if len(sent_wds) < 1:
        return None, None
    assert sum(sent_lens) == len(sent_wds)
    # 返回3个值，第一个是用空格连接的词，第二个是各句子长度，第三个是总词数
    return ' '.join(sent_wds), ' '.join(map(str, sent_lens)), len(sent_wds)


if __name__ == '__main__':
    u_columns = ['SID', '18_total_nourish', '7_SFTG', '2_UGGPA', '34_QTRCXX_DYCXMCS', '34_FKYLCG_SXSJYYJSHD',
                 '34_GJHPYCG_GJHY', '34_FKYLCG_QTFKYCG', '3_total_honor', '17_total_hlConference',
                 '34_KYLCG_QTKYCG', '7_total_level46', '3_RYCHDM', '30_total_deed', '31_total_project',
                 '34_QTRCXX_DYSWSC', '26_GJPYLX', '26_total_nourish2', '33_PJNJPM', '5_JXJDJDM',
                 '34_GJHPYCG_GJXM', '7_KSXMDM', '33_PJBJPM', '32_BRSFZYWCR', '4_total_gscholarship',
                 '34_QTRCXX_MRSWSC', '16_total_paperAward', '21_total_otherAchievement', '12_total_books',
                 '34_KYLCG_ZZ', '33_PJCJ', '24_total_book2', '32_total_nresearch', '5_total_ugscholarship',
                 '34_JCQK_GRXJSJJBD', '14_total_awards', '5_JXJDM', '25_total_iconference', '34_FKYLCG_JNRZ',
                 '12_BRZXZS', '27_total_practice', '34_KYLCG_ZL', '34_KYLCG_LW',
                 '34_KYLCG_KYXM', '24_YZ', '34_XSGZYJZGW_YJSJRFDY', '29_WYLX',
                 '24_ZZBRJS', '11_total_conference', '20_total_paper2']
    zhilian(u_columns)
    print('finished')
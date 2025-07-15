# @Time   : 2022/3/21
# @Author : Chen Yang
# @Email  : flust@ruc.edu.cn

"""
pjfbole
"""

import torch
import torch.nn as nn
from torch.nn.init import xavier_normal_

from recbole.model.abstract_recommender import GeneralRecommender
from recbole.model.init import xavier_normal_initialization
from recbole.model.loss import BPRLoss
from recbole.utils import InputType
from recbole.model.layers import MLPLayers

from torch.nn.init import xavier_normal_, xavier_uniform_

'''
这是一个自定义的注意力编码器，用于计算输入的注意力权重。
'''
class SelfAttentionEncoder(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.attn = nn.Sequential(
            nn.Linear(dim, dim),
            nn.Tanh(),
            nn.Linear(dim, 1, bias=False),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        # (N, L, D)
        a = self.attn(x)  # (N, L, 1)
        x = (x * a).sum(dim=1)  # (N, D)
        return x

'''
处理职位要求，包含一个Bi-LSTM和两个注意力编码器。
'''
class JobLayer(nn.Module):
    def __init__(self, dim, hd_size):
        super().__init__()
        self.attn1 = SelfAttentionEncoder(dim)
        self.biLSTM = nn.LSTM(
            input_size=dim,
            hidden_size=hd_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.attn2 = SelfAttentionEncoder(dim)

    def forward(self, x):
        # (N, S, L, D) batch_size,max_sent_num,max_sent_len,embedding_size
        x = x.permute(1, 0, 2, 3)  # (S, N, L, D) max_sent_num,batch_size,max_sent_len,embedding_size
        # 第一层注意力处理
        x = torch.cat([self.attn1(_).unsqueeze(0) for _ in x])  # (S, N, D)
        s = x.permute(1, 0, 2)  # (N, S, D)
        c = self.biLSTM(s)[0]  # (N, S, D)
        g = self.attn2(c)  # (N, D)
        return s, g

'''
共同注意力编码器，用于计算候选人经历和职位要求之间的关系。
'''
class CoAttentionEncoder(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.W = nn.Linear(dim, dim, bias=False)
        self.U = nn.Linear(dim, dim, bias=False)
        self.attn = nn.Sequential(
            nn.Tanh(),
            nn.Linear(dim, 1, bias=False),
            nn.Softmax(dim=0)
        )

    def forward(self, x, s):
        # (N, L, D), (N, S2, D)
        s = s.permute(1, 0, 2)  # (S2, N, D)
        y = torch.cat([self.attn(
            self.W(x.permute(1, 0, 2)) + self.U(_.expand(x.shape[1], _.shape[0], _.shape[1]))).permute(2, 0, 1)
                       for _ in s]).permute(2, 0, 1)
        # (N, D) -> (L, N, D) -> (L, N, 1) -- softmax as L --> (L, N, 1) -> (1, L, N) -> (S2, L, N) -> (N, S2, L)
        sr = torch.cat([torch.mm(y[i], _).unsqueeze(0) for i, _ in enumerate(x)])  # (N, S2, D)
        sr = torch.mean(sr, dim=1)  # (N, D)
        return sr

'''
处理候选人经历，包含一个共同注意力编码器、一个Bi-LSTM和一个自注意力编码器。
'''
class GeekLayer(nn.Module):
    def __init__(self, dim, hd_size):
        super().__init__()
        self.co_attn = CoAttentionEncoder(dim)
        self.biLSTM = nn.LSTM(
            input_size=dim,
            hidden_size=hd_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.self_attn = SelfAttentionEncoder(dim)

    def forward(self, x, s):
        # (N, S1, L, D), (N, S2, D)
        x = x.permute(1, 0, 2, 3)  # (S1, N, L, D)
        sr = torch.cat([self.co_attn(_, s).unsqueeze(0) for _ in x])  # (S1, N, D)
        u = sr.permute(1, 0, 2)  # (N, S1, D)
        c = self.biLSTM(u)[0]  # (N, S1, D)
        g = self.self_attn(c)  # (N, D)
        return g


class APJFNN(GeneralRecommender):
    input_type = InputType.PAIRWISE

    def __init__(self, config, dataset):
        super(APJFNN, self).__init__(config, dataset)
        self.USER_SENTS = config['USER_DOC_FIELD']
        self.ITEM_SENTS = config['ITEM_DOC_FIELD']
        self.neg_prefix = config['NEG_PREFIX']
        self.embedding_size = config['embedding_size']
        self.hd_size = config['hidden_size']
        self.dropout = config['dropout']

        # 词汇表的大小
        self.wd_num = len(dataset.wd2id.keys())
        # 嵌入层，将词汇表中的词转换为指定维度的向量表示
        self.emb = nn.Embedding(self.wd_num, self.embedding_size, padding_idx=0)

        # 用于处理候选人的经历和职位要求的序列数据。双向LSTM可以捕捉序列中前后文的信息。
        self.geek_biLSTM = nn.LSTM(
            input_size=self.embedding_size,
            hidden_size=self.hd_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        self.job_biLSTM = nn.LSTM(
            input_size=self.embedding_size,
            hidden_size=self.hd_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # 能力感知层 因为是双向LSTM，所以输入维度是嵌入向量维度的两倍。
        self.job_layer = JobLayer(self.hd_size * 2, self.hd_size)
        self.geek_layer = GeekLayer(self.hd_size * 2, self.hd_size)

        # 多层感知机（MLP），用于最终的匹配度计算
        self.mlp = MLPLayers(
            layers=[self.hd_size * 2 * 3, self.hd_size, 1],
            dropout=self.dropout,
            activation='tanh'
        )

        # 使用BPR损失函数，用于优化模型，使得正样本的评分高于负样本。
        self.loss = BPRLoss()

    def forward(self, interaction, geek_field, job_field):
        # 从 interaction 中获取候选人经历和职位要求的句子
        geek_sents = interaction[geek_field]    #256,20,30 batch_size,max_sent_num,max_sent_len
        job_sents = interaction[job_field]  #256,20,30
        # 将句子通过嵌入层转换为向量表示
        geek_vecs, job_vecs = self.emb(geek_sents), self.emb(job_sents) # 256,20,30,128 batch_size,max_sent_num,max_sent_len,embedding_size
        # 使用 BiLSTM 对句子向量进行处理，得到隐藏状态向量
        geek_vecs = torch.cat([self.geek_biLSTM(_)[0].unsqueeze(0) for _ in geek_vecs])
        job_vecs = torch.cat([self.job_biLSTM(_)[0].unsqueeze(0) for _ in job_vecs])

        # 使用 JobLayer 和 GeekLayer 对职位要求和候选人经历进行进一步处理，得到表示向量
        sj, gj = self.job_layer(job_vecs)   # 256 128 batch_size,max_sent_num,max_sent_len,embedding_size
        gr = self.geek_layer(geek_vecs, sj)

        # 将职位要求表示gj、候选人经历表示gr它们的差gj - gr拼接在一起
        x = torch.cat([gj, gr, gj - gr], axis=1)
        # 通过多层感知机（MLP）计算匹配度
        x = self.mlp(x).squeeze(1)
        return x

    def calculate_loss(self, interaction):
        output_pos = self.forward(interaction, self.USER_SENTS, self.ITEM_SENTS)
        output_neg = self.forward(interaction, self.USER_SENTS, self.neg_prefix + self.ITEM_SENTS)
        return self.loss(output_pos, output_neg)

    # 使用 Sigmoid 函数对前向传播的结果进行归一化，输出匹配度
    def predict(self, interaction):
        return torch.sigmoid(self.forward(interaction, self.USER_SENTS, self.ITEM_SENTS))

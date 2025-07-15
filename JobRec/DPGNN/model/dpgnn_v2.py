# @Time   : 2022/3/21
# @Author : Chen Yang
# @Email  : flust@ruc.edu.cn

"""
pjfbole
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.init import xavier_normal_
from recbole.model.abstract_recommender import GeneralRecommender
from recbole.model.loss import BPRLoss, EmbLoss
from recbole.utils import InputType

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
        self.linear = nn.Linear(hd_size * 2, dim)
        self.attn2 = SelfAttentionEncoder(hd_size * 2)

    def forward(self, x):
        # (N, S, L, D) batch_size,max_sent_num,max_sent_len,embedding_size
        x = x.permute(1, 0, 2, 3)  # (S, N, L, D) max_sent_num,batch_size,max_sent_len,embedding_size
        # 第一层注意力处理
        x = torch.cat([self.attn1(_).unsqueeze(0) for _ in x])  # (S, N, D)
        s = x.permute(1, 0, 2)  # (N, S, D)
        c = self.biLSTM(s)[0]  # (N, S, D)
        # c = self.linear(c)  # 将 hidden_size*2 维度映射到 D=768
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
        # 获取批次大小
        batch_size_x, batch_size_s = x.size(0), s.size(0)

        # 如果 x 和 s 在批次大小上不匹配，扩展较小的批次大小
        if batch_size_x != batch_size_s:
            if batch_size_x > batch_size_s:
                s = s.repeat(batch_size_x // batch_size_s + 1, 1, 1)[:batch_size_x]  # 扩展 s
            else:
                x = x.repeat(batch_size_s // batch_size_x + 1, 1, 1)[:batch_size_s]  # 扩展 x

        s = s.permute(1, 0, 2)  # (S2, N, D)
        y = torch.cat([self.attn(
            self.W(x.permute(1, 0, 2)) + self.U(_.expand(x.shape[1], _.shape[0], _.shape[1]))).permute(2, 0, 1)
                       for _ in s]).permute(2, 0, 1)

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
        self.self_attn_1 = SelfAttentionEncoder(dim)
        self.biLSTM = nn.LSTM(
            input_size=dim,
            hidden_size=hd_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.linear = nn.Linear(hd_size * 2, dim)
        self.self_attn_2 = SelfAttentionEncoder(hd_size * 2)

    def forward(self, x, s):
        # (N, S1, L, D), (N, S2, D)
        x = x.permute(1, 0, 2, 3)  # (S1, N, L, D)
        # x = torch.cat([self.self_attn_1(_).unsqueeze(0) for _ in x])  # (S, N, D)
        sr = torch.cat([self.co_attn(_, s).unsqueeze(0) for _ in x])  # (S1, N, D)
        u = sr.permute(1, 0, 2)  # (N, S1, D)
        c = self.biLSTM(u)[0]  # (N, S1, D)
        # c = self.linear(c)  # 将 hidden_size*2 维度映射到 D=768
        g = self.self_attn_2(c)  # (N, D)
        return g


'''
DPGNN 模型主类
'''


class DPGNN(GeneralRecommender):
    # 输入类型为“成对输入”
    input_type = InputType.PAIRWISE

    def __init__(self, config, dataset):
        super(DPGNN, self).__init__(config, dataset)

        from recbole_pjf.model.layer import GCNConv

        # 负样本用户和项目ID
        self.NEG_USER_ID = config['NEG_PREFIX'] + self.USER_ID  # neg_user_id
        self.NEG_ITEM_ID = config['NEG_PREFIX'] + self.ITEM_ID  # neg_job_id

        # 嵌入大小
        self.embedding_size = config['embedding_size']  # 128

        '''
        1、加载数据集信息（交互矩阵、用户单向交互、项目单向交互）
        '''
        self.interaction_matrix = dataset.inter_matrix(form='coo').astype(np.float32)  # 表示用户与项目的所有交互关系
        self.user_add_matrix = dataset.user_single_inter_matrix(form='coo').astype(np.float32)  # 用户的单向交互
        self.job_add_matrix = dataset.item_single_inter_matrix(form='coo').astype(np.float32)  # 工作HR的单向交互
        # print("self.interaction_matrix:", self.interaction_matrix)
        # print("self.user_add_matrix:", self.user_add_matrix)
        # print("self.job_add_matrix:", self.job_add_matrix)
        # print(self.interaction_matrix.shape[0]) # 4501
        # print(self.user_add_matrix.shape[0])
        # print(self.job_add_matrix.shape[0])

        '''
        2、加载参数信息
        '''
        self.latent_dim = config['embedding_size']  # int type: lightGCN的嵌入维度
        self.n_layers = config['n_layers']  # int type: lightGCN的层数
        self.reg_weight = config['reg_weight']  # float32 type: l2 归一化的权重衰减
        self.mul_weight = config['mutual_weight']
        self.temperature = config['temperature']
        self.hd_size = config['hidden_size']
        self.dropout = config['dropout']

        '''
        3、初始化嵌入层
        '''
        # 初始化嵌入层，用于用户和职位的嵌入向量
        self.user_embedding_a = nn.Embedding(self.n_users, self.latent_dim)  # 用户主动选择偏好嵌入
        self.item_embedding_a = nn.Embedding(self.n_items, self.latent_dim)  # 项目主动选择偏好嵌入
        self.user_embedding_p = nn.Embedding(self.n_users, self.latent_dim)  # 用户被动选择偏好嵌入
        self.item_embedding_p = nn.Embedding(self.n_items, self.latent_dim)  # 项目被动选择偏好嵌入
        # print("self.n_users:", self.n_users) # 4501
        # print("self.n_items:", self.n_items) # 19386
        # print("self.user_embedding_a:", self.user_embedding_a)

        # 初始化图卷积层
        self.gcn_conv = GCNConv(dim=self.latent_dim)
        # 初始化损失函数
        self.mf_loss = BPRLoss()
        self.reg_loss = EmbLoss()
        self.mutual_loss = nn.CrossEntropyLoss()
        self.loss = 0

        '''
        4、初始化BERT
        '''
        self.ADD_BERT = config['ADD_BERT']
        # 设置BERT输出尺寸
        self.BERT_e_size = config['BERT_output_size'] or 1
        #  初始化BERT线性变换层
        # self.bert_lr = nn.Linear(config['BERT_embedding_size'], self.BERT_e_size)
        self.bert_lr = nn.Linear(self.hd_size * 2, self.BERT_e_size)
        if self.ADD_BERT:
            # 加载用户和项目的BERT嵌入数据，并将其转换到指定的设备上（如GPU）
            self.bert_user = dataset.bert_user.to(config['device'])
            self.bert_item = dataset.bert_item.to(config['device'])

        '''
        5、初始化能力感知层
        '''
        # 能力感知层 因为是双向LSTM，所以输入维度是嵌入向量维度的两倍。
        self.job_layer = JobLayer(config['BERT_embedding_size'], self.hd_size)
        self.geek_layer = GeekLayer(config['BERT_embedding_size'], self.hd_size)

        '''
        6、从交互矩阵构建邻接矩阵并进行归一化（使用拉普拉斯矩阵）
        self.edge_index：图的边索引
        self.edge_weight：图的边权重
        '''
        # 获取归一化的邻接矩阵
        self.edge_index, self.edge_weight = self.get_norm_adj_mat()
        # 将数据移动到指定设备
        self.edge_index = self.edge_index.to(config['device'])
        self.edge_weight = self.edge_weight.to(config['device'])

        '''
        6、遍历模型中的所有层应用自定义的初始化方法 _init_weights
        '''
        self.apply(self._init_weights)

    '''
    初始化模型中的嵌入层权重
    '''

    def _init_weights(self, module):
        if isinstance(module, nn.Embedding):
            # 这是 PyTorch 提供的 Xavier 正态初始化方法，用于初始化神经网络的权重。
            # 该方法会根据层的输入和输出节点数，生成均值为 0、方差为特定值的正态分布随机数。
            xavier_normal_(module.weight.data)

    '''
    归一化邻接矩阵计算
    从训练数据构建一个图的邻接矩阵并对其进行归一化（使用拉普拉斯矩阵）
    '''

    def get_norm_adj_mat(self):
        r"""Get the normalized interaction matrix of users and items.
        Construct the square matrix from the training data and normalize it
        using the laplace matrix.
        .. math::
            A_{hat} = D^{-0.5} \times A \times D^{-0.5}
        Returns:
            The normalized interaction matrix in Tensor.
        """
        #   user a node: [0 ~~~ n_users] (len: n_users)
        #   item p node: [n_users + 1 ~~~ n_users + 1 + n_items] (len: n_users)
        #   user p node: [~] (len: n_users)
        #   item a node: [~] (len: n_items)

        '''
            示例：
            row = np.array([0, 1, 2])   用户索引
            col = np.array([0, 1, 0])   工作索引
            n_users = 3
            n_items = 2

            ## 从交互矩阵中提取行和列索引
            # row: tensor([0, 1, 2])
            # col: tensor([3, 4, 3])

            ## 构建边索引
            # edge_index1: tensor([[0, 1, 2], [3, 4, 3]])
            # edge_index2: tensor([[3, 4, 3], [0, 1, 2]])
            # edge_index3: tensor([[5, 6, 7], [8, 9, 8]])
            # edge_index4: tensor([[8, 9, 8], [5, 6, 7]])

            ## 合并所有边索引
            # edge_index_suc: tensor([[0, 1, 2, 3, 4, 3, 5, 6, 7, 8, 9, 8],
            #                         [3, 4, 3, 0, 1, 2, 8, 9, 8, 5, 6, 7]])

            ## 转换为交互的形式
            # 0 -> 3
            # 1 -> 4
            # 2 -> 3
            ...
            # 8 -> 7
        '''
        from torch_geometric.utils import degree
        n_all = self.n_users + self.n_items

        # success edge
        # 从交互矩阵中提取行和列索引
        row = torch.LongTensor(self.interaction_matrix.row)  # 用户索引
        col = torch.LongTensor(self.interaction_matrix.col) + self.n_users  # 工作索引 = 用户交互过的工作索引 + 用户数
        # 构建交互边
        edge_index1 = torch.stack([row, col])  # 用户到工作的边
        edge_index2 = torch.stack([col, row])  # 工作到用户的边
        edge_index3 = torch.stack([row + n_all, col + n_all])
        edge_index4 = torch.stack([col + n_all, row + n_all])
        # 合并所有边索引
        edge_index_suc = torch.cat([edge_index1, edge_index2, edge_index3, edge_index4], dim=1)

        # user_add edge
        row = torch.LongTensor(self.user_add_matrix.row)
        col = torch.LongTensor(self.user_add_matrix.col) + self.n_users
        edge_index1 = torch.stack([row, col])
        edge_index2 = torch.stack([col, row])
        edge_index_user_add = torch.cat([edge_index1, edge_index2], dim=1)

        # job_add edge
        row = torch.LongTensor(self.job_add_matrix.row)
        col = torch.LongTensor(self.job_add_matrix.col) + self.n_users
        edge_index1 = torch.stack([row + n_all, col + n_all])
        edge_index2 = torch.stack([col + n_all, row + n_all])
        edge_index_job_add = torch.cat([edge_index1, edge_index2], dim=1)

        # self edge
        # 用户节点的索引，从 0 到 self.n_users - 1
        geek = torch.LongTensor(torch.arange(0, self.n_users))
        # job节点的索引，从 self.n_users 到 self.n_users + self.n_items - 1
        job = torch.LongTensor(torch.arange(0, self.n_items) + self.n_users)
        edge_index_geek_1 = torch.stack([geek, geek + n_all])
        edge_index_geek_2 = torch.stack([geek + n_all, geek])
        edge_index_job_1 = torch.stack([job, job + n_all])
        edge_index_job_2 = torch.stack([job + n_all, job])
        edge_index_self = torch.cat([edge_index_geek_1, edge_index_geek_2, edge_index_job_1, edge_index_job_2], dim=1)

        # 合并所有边
        edge_index = torch.cat([edge_index_suc, edge_index_user_add, edge_index_job_add, edge_index_self], dim=1)

        # 计算归一化系数
        ## 计算度数 deg，即每个节点的连接数
        deg = degree(edge_index[0], (self.n_users + self.n_items) * 2)
        ## 计算归一化系数 norm_deg，对于度数为零的节点，将其度数设置为1，以避免除零错误
        norm_deg = 1. / torch.sqrt(torch.where(deg == 0, torch.ones([1]), deg))

        # 计算边权重
        edge_weight = norm_deg[edge_index[0]] * norm_deg[edge_index[1]]
        # 返回边索引和边权重
        return edge_index, edge_weight

    '''
    用于获取用户和项目的嵌入，并将这些嵌入合并成一个嵌入矩阵。
    '''

    def get_ego_embeddings(self):
        r"""Get the embedding of users and items and combine to an embedding matrix.

        Returns:
            Tensor of the embedding matrix. Shape of [n_items+n_users, embedding_dim]
        """
        # 获取用户和项目的偏好嵌入权重
        user_embeddings_a = self.user_embedding_a.weight
        item_embeddings_a = self.item_embedding_a.weight
        user_embeddings_p = self.user_embedding_p.weight
        item_embeddings_p = self.item_embedding_p.weight
        # 合并用户和项目的偏好嵌入
        ego_embeddings = torch.cat([user_embeddings_a,
                                    item_embeddings_p,
                                    user_embeddings_p,
                                    item_embeddings_a], dim=0)

        if self.ADD_BERT:
            # 通过线性层转换后的用户和项目BERT嵌入
            # print("self.bert_user.shape:", self.bert_user.shape)
            # print("self.bert_item.shape:", self.bert_item.shape)
            bert_item_expanded = self.bert_item.unsqueeze(1).unsqueeze(2)
            bert_user_expanded = self.bert_user.unsqueeze(1).unsqueeze(2)
            # 使用 JobLayer 和 GeekLayer 对职位要求和候选人经历进行进一步处理，得到表示向量
            sj, gj = self.job_layer(bert_item_expanded)
            gr = self.geek_layer(bert_user_expanded, sj)

            self.bert_i = self.bert_lr(gj)
            self.bert_u = self.bert_lr(gr)
            # print("self.bert_u.shape:", self.bert_u.shape)
            # print("self.bert_i.shape:", self.bert_i.shape)
            # 将用户和项目的BERT嵌入按维度0拼接，形成 bert_e 矩阵
            bert_e = torch.cat([self.bert_u,
                                self.bert_i,
                                self.bert_u,
                                self.bert_i], dim=0)
            # 将原始嵌入 ego_embeddings 和 BERT嵌入 bert_e 按维度1（列）拼接，返回最终的嵌入矩阵。
            # print("ego_embeddings.shape:", ego_embeddings.shape)
            # print("bert_e.shape:", bert_e.shape)
            return torch.cat([ego_embeddings, bert_e], dim=1)

        return ego_embeddings

    '''
    InfoNCE 损失计算
    '''

    def info_nce_loss(self, index, is_user):
        all_embeddings = self.get_ego_embeddings()
        user_e_a, item_e_p, user_e_p, item_e_a = torch.split(all_embeddings,
                                                             [self.n_users, self.n_items, self.n_users, self.n_items])
        if is_user:
            u_e_a = F.normalize(user_e_a[index], dim=1)
            u_e_p = F.normalize(user_e_p[index], dim=1)
            similarity_matrix = torch.matmul(u_e_a, u_e_p.T)
        else:
            i_e_a = F.normalize(item_e_a[index], dim=1)
            i_e_p = F.normalize(item_e_p[index], dim=1)
            similarity_matrix = torch.matmul(i_e_a, i_e_p.T)

        mask = torch.eye(index.shape[0], dtype=torch.bool).to(self.device)

        positives = similarity_matrix[mask].view(index.shape[0], -1)
        negatives = similarity_matrix[~mask].view(index.shape[0], -1)

        logits = torch.cat([positives, negatives], dim=1)
        labels = torch.zeros(logits.shape[0], dtype=torch.long).to(self.device)
        logits = logits / self.temperature

        return logits, labels

    '''
    前向传播过程
    这个方法通过多层图卷积操作（GCN）来计算用户和项目的嵌入，并将结果返回
    '''

    def forward(self):
        # 获取初始嵌入
        all_embeddings = self.get_ego_embeddings()
        embeddings_list = [all_embeddings]

        # 多层图卷积操作
        # 这个循环遍历每一层图卷积，将每层的嵌入结果存入 embeddings_list 中
        for layer_idx in range(self.n_layers):
            all_embeddings = self.gcn_conv(all_embeddings, self.edge_index, self.edge_weight)
            embeddings_list.append(all_embeddings)

        # 堆叠和平均嵌入
        lightgcn_all_embeddings = torch.stack(embeddings_list, dim=1)
        lightgcn_all_embeddings = torch.mean(lightgcn_all_embeddings, dim=1)

        # 分割嵌入矩阵
        # 将最终的嵌入矩阵分割成用户和项目的不同部分
        user_e_a, item_e_p, user_e_p, item_e_a = torch.split(lightgcn_all_embeddings,
                                                             [self.n_users, self.n_items, self.n_users, self.n_items])
        return user_e_a, item_e_p, user_e_p, item_e_a

    def calculate_loss(self, interaction):
        user = interaction[self.USER_ID]
        item = interaction[self.ITEM_ID]
        neg_user = interaction[self.NEG_USER_ID]
        neg_item = interaction[self.NEG_ITEM_ID]

        user_e_a, item_e_p, user_e_p, item_e_a = self.forward()

        # user active
        u_e_a = user_e_a[user]
        n_u_e_a = user_e_a[neg_user]
        # item negative
        i_e_p = item_e_p[item]
        n_i_e_p = item_e_p[neg_item]

        # user negative
        u_e_p = user_e_p[user]
        n_u_e_p = user_e_p[neg_user]
        # item active
        i_e_a = item_e_a[item]
        n_i_e_a = item_e_a[neg_item]

        r_pos = torch.mul(u_e_a, i_e_p).sum(dim=1)
        s_pos = torch.mul(u_e_p, i_e_a).sum(dim=1)

        r_neg1 = torch.mul(u_e_a, n_i_e_p).sum(dim=1)
        s_neg1 = torch.mul(u_e_p, n_i_e_a).sum(dim=1)

        r_neg2 = torch.mul(n_u_e_a, i_e_p).sum(dim=1)
        s_neg2 = torch.mul(n_u_e_p, i_e_a).sum(dim=1)

        mf_loss_u = self.mf_loss(2 * r_pos + 2 * s_pos, r_neg1 + s_neg1 + r_neg2 + s_neg2)

        # calculate Emb Loss
        u_ego_embeddings_a = self.user_embedding_a(user)
        u_ego_embeddings_p = self.user_embedding_p(user)
        pos_ego_embeddings_a = self.item_embedding_a(item)
        pos_ego_embeddings_p = self.item_embedding_p(item)
        neg_ego_embeddings_a = self.item_embedding_a(neg_item)
        neg_ego_embeddings_p = self.item_embedding_p(neg_item)
        neg_u_ego_embeddings_a = self.user_embedding_a(neg_user)
        neg_u_ego_embeddings_p = self.user_embedding_p(neg_user)

        reg_loss = self.reg_loss(u_ego_embeddings_a, u_ego_embeddings_p,
                                 pos_ego_embeddings_a, pos_ego_embeddings_p,
                                 neg_ego_embeddings_a, neg_ego_embeddings_p,
                                 neg_u_ego_embeddings_a, neg_u_ego_embeddings_p)

        loss = mf_loss_u + self.reg_weight * reg_loss

        logits_user, labels = self.info_nce_loss(user, is_user=True)
        loss += self.mul_weight * self.mutual_loss(logits_user, labels)

        logits_job, labels = self.info_nce_loss(item, is_user=False)
        loss += self.mul_weight * self.mutual_loss(logits_job, labels)

        return loss

    # 预测用户对项目的偏好分数
    def predict(self, interaction):
        # 提取用户和项目ID
        user = interaction[self.USER_ID]
        item = interaction[self.ITEM_ID]

        #  计算用户和项目的嵌入
        user_e_a, item_e_p, user_e_p, item_e_a = self.forward()

        # user activate
        u_e_a = user_e_a[user]
        # item negative
        i_e_p = item_e_p[item]

        # user negative
        u_e_p = user_e_p[user]
        # print("u_e_p:", u_e_a.shape)
        # item negative
        i_e_a = item_e_a[item]
        # print("i_e_a:", i_e_a.shape)

        # 计算用户主动嵌入和项目被动嵌入的元素乘积，并对其进行求和
        I_geek = torch.mul(u_e_a, i_e_p).sum(dim=1)
        I_job = torch.mul(u_e_p, i_e_a).sum(dim=1)
        # I_geek = torch.mul(u_e_a, i_e_p)
        # I_job = torch.mul(u_e_p, i_e_a)

        # calculate BPR Loss
        # 计算最终分数
        scores = I_geek + I_job

        return scores






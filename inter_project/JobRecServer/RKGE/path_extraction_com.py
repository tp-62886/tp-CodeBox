# Build knowledge graph and mine the connected paths between users and movies in the training data of MovieLens

import argparse
import networkx as nx
import random


def load_data(file):
    '''
    load training (positive) or negative user-movie interaction data

    Input:
        @file: training (positive) data or negative data

    Output:
        @data: pairs containing positive or negative interaction data
    '''
    data = []

    for line in file:
        lines = line.split(' ')
        user = lines[0]
        work = lines[1].replace('\n', '')
        data.append((user, work))
        # print(len(data))
    return data


def add_user_movie_interaction_into_graph(positive_rating):
    '''
    add user-movie interaction data into the graph

    Input:
        @pos_rating: user-movie interaction data

    Output:
        @Graph: the built graph with user-movie interaction info
    '''
    print(f"positive_pair个数:{len(positive_rating)}")
    Graph = nx.DiGraph()

    for pair in positive_rating:
        user = pair[0]
        work = pair[1]
        user_node = 'u' + user
        work_node = 'i' + work
        Graph.add_node(user_node)
        Graph.add_node(work_node)
        Graph.add_edge(user_node, work_node)

    return Graph


def add_auxiliary_into_graph(fr_auxiliary, Graph):
    '''
    add auxiliary information (e.g., actor, director, genre) into graph

    Input:
        @fr_auxiliary: auxiliary mapping information about works
        @Graph: the graph with user-work interaction info

    Output:
        @Graph: the graph with user-work interaction and auxiliary info
    '''

    for line in fr_auxiliary:
        lines = line.replace('\n', '').split('|')
        if len(lines) != 4: continue

        work_id = lines[0]
        DWHYMC_list = lines[1]
        DWXZMC_list = lines[2]
        GZZWLBMC_list = lines[3]
        # print(work_id,DWHYMC_list,DWXZMC_list,GZZWLBMC_list)

        # add work nodes into Graph, in case the movie is not included in the training data
        work_node = 'i' + work_id
        if not Graph.has_node(work_node):
            Graph.add_node(work_node)

        # add the DWHYMC nodes into the graph;
        # as DWHYMC connection is too dense, we add one genre to avoid over-emphasizing its effect
        DWHYMC_id = DWHYMC_list
        DWHYMC_node = 'a' + DWHYMC_id
        if not Graph.has_node(DWHYMC_node):
            Graph.add_node(DWHYMC_node)
        Graph.add_edge(work_node, DWHYMC_node)
        Graph.add_edge(DWHYMC_node, work_node)

        # add the director nodes into the graph
        DWXZMC_id = DWXZMC_list
        DWXZMC_node = 'b' + DWXZMC_id
        if not Graph.has_node(DWXZMC_node):
            Graph.add_node(DWXZMC_node)
        Graph.add_edge(work_node, DWXZMC_node)
        Graph.add_edge(DWXZMC_node, work_node)

        # add the actor nodes into the graph
        GZZWLBMC_id = GZZWLBMC_list
        GZZWLBMC_node = 'c' + GZZWLBMC_id
        if not Graph.has_node(GZZWLBMC_node):
            Graph.add_node(GZZWLBMC_node)
        Graph.add_edge(work_node, GZZWLBMC_node)
        Graph.add_edge(GZZWLBMC_node, work_node)

    return Graph


def print_graph_statistic(Graph):
    '''
    output the statistic info of the graph

    Input:
        @Graph: the built graph
    '''
    print('The knowledge graph has been built completely \n')
    print('The number of nodes is:  ' + str(len(Graph.nodes())) + ' \n')
    print('The number of edges is  ' + str(len(Graph.edges())) + ' \n')


def mine_paths_between_nodes(Graph, user_node, work_node, maxLen, sample_size, fw_file):
    '''
    mine qualified paths between user and movie nodes, and get sampled paths between nodes

    Inputs:
        @user_node: user node
        @movie_node: movie node
        @maxLen: path length
        @fw_file: the output file for the mined paths
    '''

    connected_path = []  # 只保存从user_node到work_node路径中长度为maxLen + 1的路径
    for path in nx.all_simple_paths(Graph, source=user_node, target=work_node, cutoff=maxLen):
        # print(f"path_len:{len(path)}")
        if len(path) == maxLen + 1:
            connected_path.append(path)
        if len(connected_path) >= sample_size:
            break

    path_size = len(connected_path)
    # print(f"pathsize:{path_size}")

    # as there is a huge number of paths connected user-movie nodes, we get randomly sampled paths
    # random sample can better balance the data distribution and model complexity
    if path_size > sample_size:  # 只需要保留sample_size个路径
        random.shuffle(connected_path)
        connected_path = connected_path[:sample_size]

    for path in connected_path:  # 将connected_path中所有路径保存
        line = ",".join(path) + '\n'
        fw_file.write(line)
        # print("写入一条数据")

    # print('The number of paths between '+ user_node + ' and ' + movie_node + ' is: ' +  str(len(connected_path)) +'\n')


def dump_paths(Graph, rating_pair, maxLen, sample_size, fw_file):
    '''
    dump the postive or negative paths

    Inputs:
        @Graph: the well-built knowledge graph
        @rating_pair: positive_rating or negative_rating
        @maxLen: path length
        @sample_size: size of sampled paths between user-movie nodes
    '''
    num = 0
    idx = 1
    for pair in rating_pair:
        print(f"进度:{idx}/{len(rating_pair)}")
        idx = idx + 1
        user_id = pair[0]
        work_id = pair[1]
        user_node = 'u' + user_id
        work_node = 'i' + work_id
        # 对于每对(major,work)，从知识图谱中找sample_size条长度为maxLen+1的路径，并将这些路径写入fw_file文件

        if Graph.has_node(user_node) and Graph.has_node(work_node):
            num = num + 1
            mine_paths_between_nodes(Graph, user_node, work_node, maxLen, sample_size, fw_file)
    print(num)

def main(training_file, negative_file, auxiliary_file, positive_path, negative_path, path_length, sample_size):
    with open(training_file, 'r', encoding='Windows-1252') as fr_training:
        positive_rating = load_data(fr_training)
    with open(negative_file, 'r') as fr_negative:
        negative_rating = load_data(fr_negative)
    with open(auxiliary_file, 'r') as fr_auxiliary:
        Graph = add_user_movie_interaction_into_graph(positive_rating)
        Graph = add_auxiliary_into_graph(fr_auxiliary, Graph)

    print_graph_statistic(Graph)

    with open(positive_path, 'w') as fw_positive_path:
        print("正在生成positive_path...")
        dump_paths(Graph, positive_rating, path_length, sample_size, fw_positive_path)

    with open(negative_path, 'w') as fw_negative_path:
        print("正在生成negative_path...")
        dump_paths(Graph, negative_rating, path_length, sample_size, fw_negative_path)
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description=''' Build Knowledge Graph and Mine the Connected Paths''')
#
#     parser.add_argument('--training', type=str, dest='training_file', default='data/xdu/training_com.txt')
#     parser.add_argument('--negtive', type=str, dest='negative_file', default='data/xdu/negative_com.txt')
#     parser.add_argument('--auxiliary', type=str, dest='auxiliary_file', default='data/xdu/auxiliary-mapping-com.txt')
#     parser.add_argument('--positivepath', type=str, dest='positive_path', default='data/xdu/positive-path_com.txt', \
#                         help='paths between user-item interaction pairs')
#     parser.add_argument('--negativepath', type=str, dest='negative_path', default='data/xdu/negative-path_com.txt', \
#                         help='paths between negative sampled user-item pair')
#     parser.add_argument('--pathlength', type=int, dest='path_length', default=3,
#                         help='length of paths with choices [3,5,7]')
#     parser.add_argument('--samplesize', type=int, dest='sample_size', default=5, \
#                         help='the sampled size of paths bwteen nodes with choices [5, 10, 20, ...]')
#
#     parsed_args = parser.parse_args()
#
#     training_file = parsed_args.training_file
#     negative_file = parsed_args.negative_file
#     auxiliary_file = parsed_args.auxiliary_file
#     positive_path = parsed_args.positive_path
#     negative_path = parsed_args.negative_path
#     path_length = parsed_args.path_length
#     sample_size = parsed_args.sample_size
#
#     fr_training = open(training_file, 'r', encoding='Windows-1252')
#     fr_negative = open(negative_file, 'r', encoding='Windows-1252')
#     fr_auxiliary = open(auxiliary_file, 'r')
#     fw_positive_path = open(positive_path, 'w')
#     fw_negative_path = open(negative_path, 'w')
#
#     positive_rating = load_data(fr_training)  # [(user,item),...]
#     # print(len(positive_rating))
#     negative_rating = load_data(fr_negative)  # [(user,item),...]
#     # print(len(negative_rating))
#     print('The number of major-work interaction data is:  ' + str(len(positive_rating)) + ' \n')
#     print('The number of negative sampled data is:  ' + str(len(negative_rating)) + ' \n')
#
#     # 根据positive_rating的[(user,item),...]，构图nx.DiGraph()建立节点和边,
#     Graph = add_user_movie_interaction_into_graph(positive_rating)
#     # print_graph_statistic(Graph)
#     Graph = add_auxiliary_into_graph(fr_auxiliary, Graph)
#     print_graph_statistic(Graph)
#
#     print("正在生成positive_path...")
#     dump_paths(Graph, positive_rating, path_length, sample_size, fw_positive_path)
#     print("正在生成negative_path...")
#     dump_paths(Graph, negative_rating, path_length, sample_size, fw_negative_path)
#
#     fr_training.close()
#     fr_negative.close()
#     fr_auxiliary.close()
#     fw_positive_path.close()
#     fw_negative_path.close()
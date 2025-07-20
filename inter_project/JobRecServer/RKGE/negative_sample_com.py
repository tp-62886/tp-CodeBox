# This is used to sample negative movies that user has not interactions with, so as to balance model training process

import argparse
import math
from random import randint


def load_data(file):
    '''
    load training data

    Input:
        @file: training data

    Outputs:
        @train_dict: user-specific training data
        @item_list: all items in the training data
    '''
    train_dict = {}
    all_work_list = []

    for line in file:
        lines = line.split(' ')
        user = lines[0]
        work = lines[1].replace('\n', '')

        if user not in train_dict:
            init_work_list = []
            init_work_list.append(work)
            train_dict.update({user: init_work_list})
        else:
            train_dict[user].append(work)

        if work not in all_work_list:
            all_work_list.append(work)

    return train_dict, all_work_list


def negative_sample(train_dict, all_work_list, shrink, fw_negative):
    '''
    sample negative movies for all users in training data

    Inputs:
        @train_dict: user-specific training data
        @all_movie_list: all the movies in the training data
    '''
    all_work_size = len(all_work_list)

    for user in train_dict:
        user_train_work = train_dict[user]
        user_train_work_size = len(user_train_work)
        negative_size = math.ceil(user_train_work_size * shrink)
        user_negative_work = []

        while (len(user_negative_work) < negative_size):
            negative_index = randint(0, (all_work_size - 1))
            negative_work = str(all_work_list[negative_index])
            if negative_work not in user_train_work and negative_work not in user_negative_work:
                user_negative_work.append(negative_work)
                line = user + ' ' + negative_work + '\n'
                fw_negative.write(line)


def main(train_file, negative_file, shrink):
    with open(train_file, 'r', encoding='Windows-1252') as fr_train:
        train_dict, all_movie_list = load_data(fr_train)
    with open(negative_file, 'w', encoding='ascii') as fw_negative:
        negative_sample(train_dict, all_movie_list, shrink, fw_negative)
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description=''' Sample Negative Movies for Each User''')
#
#     parser.add_argument('--train', type=str, dest='train_file', default='data/xdu/training_com.txt')
#     parser.add_argument('--negative', type=str, dest='negative_file', default='data/xdu/negative_com.txt')
#     parser.add_argument('--shrink', type=float, dest='shrink', default=0.05)
#
#     parsed_args = parser.parse_args()
#
#     train_file = parsed_args.train_file
#     negative_file = parsed_args.negative_file
#     shrink = parsed_args.shrink
#
#     fr_train = open(train_file, 'r', encoding='Windows-1252')
#     fw_negative = open(negative_file, 'w', encoding='Windows-1252')
#
#     train_dict, all_movie_list = load_data(fr_train)
#     negative_sample(train_dict, all_movie_list, shrink, fw_negative)
#
#     fr_train.close()
#     fw_negative.close()
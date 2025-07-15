import argparse
import operator

def round_int(rating_num, ratio):
    '''
    get the size of training data for each user
    Inputs:
        @rating_num: the total number of ratings for a specific user
        @ration: the percentage for training data
    Output:
        @train_size: the size of training data
    '''
    train_size = int(round(rating_num * ratio, 0))
    return train_size

def load_data(fr_rating):
    '''
    load the user-item rating data with the timestamp
    Input:
        @fr_rating: the user-item rating data
    Output:
        @rating_data: user-specific rating data with timestamp
    '''
    rating_data = {}
    for line in fr_rating:
        lines = line.strip().split(' ')
        user = lines[0]
        item = lines[1]
        # time = lines[3].replace('\n', '')

        if user in rating_data:
            rating_data[user].update({item: 1})
        else:
            rating_data.update({user: {item: 1}})

    return rating_data

def split_rating_into_train_test(rating_data, fw_train, fw_test, ratio):
    '''
    split rating_rating data into training and test data by timestamp
    Inputs:
        @rating_data: the user-specific rating data
        @fw_train: the training data file
        @fw_test: the test data file
        @ratio: the percentage of training data
    '''
    total_train = 0
    total_test = 0

    for user in rating_data:
        item_list = rating_data[user]
        sorted_u = sorted(item_list.items(), key=operator.itemgetter(1))
        sorted_u = dict(sorted_u)
        rating_num = len(rating_data[user])
        train_size = round_int(rating_num, ratio)
        flag = 0

        for item in sorted_u:
            num = str(sorted_u[item])
            if flag < train_size:
                line = user + ' ' + item + ' ' + num + '\n'
                fw_train.write(line)
                total_train += 1
                flag += 1
            else:
                line = user + ' ' + item + ' ' + num + '\n'
                fw_test.write(line)
                total_test += 1

    print(f"Total training entries: {total_train}")
    print(f"Total testing entries: {total_test}")

def main(rating_file, train_file, test_file, ratio):
    with open(rating_file, 'r', encoding='utf-8') as fr_rating:
        rating_data = load_data(fr_rating)

    with open(train_file, 'w', encoding='utf-8') as fw_train, open(test_file, 'w', encoding='utf-8') as fw_test:
        split_rating_into_train_test(rating_data, fw_train, fw_test, ratio)
import argparse

def mapping(fr_auxiliary, fw_mapping):
    '''
    mapping the auxiliary info (e.g., genre, director, actor) into ID

    Inputs:
        @fr_auxiliary: the auxiliary infomation
        @fw_mapping: the auxiliary mapping information
    '''
    DWHYMC_map = {}
    DWXZMC_map = {}
    GZZWLBMC_map = {}

    DWHYMC_count = DWXZMC_count = GZZWLBMC_count = 0

    for line in fr_auxiliary:
        lines = line.replace('\n', '').split('|')
        if len(lines) != 4:
            continue

        work_id = lines[0].split(':')[1]
        DWHYMC_list = []  # 单位行业，如信息传输、软件和信息技术服务业
        DWXZMC_list = []  # 单位性质名称，如外商投资企业
        GZZWLBMC_list = []  # 工作职位类别名称，如工程技术人员

        for DWHYMC in lines[1].split(":")[1].split(','):
            if DWHYMC not in DWHYMC_map:
                DWHYMC_map.update({DWHYMC: DWHYMC_count})
                DWHYMC_list.append(DWHYMC_count)
                DWHYMC_count += 1
            else:
                DWHYMC_id = DWHYMC_map[DWHYMC]
                DWHYMC_list.append(DWHYMC_id)

        for DWXZMC in lines[2].split(":")[1].split(','):
            if DWXZMC not in DWXZMC_map:
                DWXZMC_map.update({DWXZMC: DWXZMC_count})
                DWXZMC_list.append(DWXZMC_count)
                DWXZMC_count += 1
            else:
                DWXZMC_id = DWXZMC_map[DWXZMC]
                DWXZMC_list.append(DWXZMC_id)

        for GZZWLBMC in lines[3].split(':')[1].split(','):
            if GZZWLBMC not in GZZWLBMC_map:
                GZZWLBMC_map.update({GZZWLBMC: GZZWLBMC_count})
                GZZWLBMC_list.append(GZZWLBMC_count)
                GZZWLBMC_count += 1
            else:
                GZZWLBMC_id = GZZWLBMC_map[GZZWLBMC]
                GZZWLBMC_list.append(GZZWLBMC_id)

        DWHYMC_list = ",".join(map(str, DWHYMC_list))
        DWXZMC_list = ",".join(map(str, DWXZMC_list))
        GZZWLBMC_list = ",".join(map(str, GZZWLBMC_list))

        output_line = work_id + '|' + DWHYMC_list + '|' + DWXZMC_list + '|' + GZZWLBMC_list + '\n'
        fw_mapping.write(output_line)

    return DWHYMC_count, DWXZMC_count, GZZWLBMC_count

def print_statistic_info(DWHYMC_count, DWXZMC_count, GZZWLBMC_count):
    '''
    print the number of genre, director and actor
    '''
    print('The number of DWHYMC is: ' + str(DWHYMC_count))
    print('The number of DWXZMC is: ' + str(DWXZMC_count))
    print('The number of GZZWLBMC is: ' + str(GZZWLBMC_count))

def main(auxiliary_file='data/xdu/auxiliary.txt', mapping_file='data/xdu/auxiliary-mapping.txt'):
    fr_auxiliary = open(auxiliary_file, 'r', encoding='utf-8')
    fw_mapping = open(mapping_file, 'w')

    DWHYMC_count, DWXZMC_count, GZZWLBMC_count = mapping(fr_auxiliary, fw_mapping)
    print_statistic_info(DWHYMC_count, DWXZMC_count, GZZWLBMC_count)

    fr_auxiliary.close()
    fw_mapping.close()




#
# # This is used to map the auxiliary information (genre, director and actor) into mapping ID for MovieLens
#
# import argparse
#
#
# def mapping(fr_auxiliary, fw_mapping):
#     '''
#     mapping the auxiliary info (e.g., genre, director, actor) into ID
#
#     Inputs:
#         @fr_auxiliary: the auxiliary infomation
#         @fw_mapping: the auxiliary mapping information
#     '''
#     DWHYMC_map = {}
#     DWXZMC_map = {}
#     GZZWLBMC_map = {}
#     # actor_map = {}
#     # director_map = {}
#     # genre_map = {}
#
#     # actor_count = director_count = genre_count = 0
#     DWHYMC_count = DWXZMC_count = GZZWLBMC_count = 0
#
#     for line in fr_auxiliary:
#
#         lines = line.replace('\n', '').split('|')
#         if len(lines) != 4:
#             continue
#
#         # movie_id = lines[0].split(':')[1]
#         work_id = lines[0].split(':')[1]
#         DWHYMC_list = []  # 单位行业，如信息传输、软件和信息技术服务业
#         DWXZMC_list = []  # 单位性质名称，如外商投资企业
#         GZZWLBMC_list = []  # 工作职位类别名称，如工程技术人员
#
#         for DWHYMC in lines[1].split(":")[1].split(','):
#             if DWHYMC not in DWHYMC_map:
#                 DWHYMC_map.update({DWHYMC: DWHYMC_count})
#                 DWHYMC_list.append(DWHYMC_count)
#                 DWHYMC_count = DWHYMC_count + 1
#             else:
#                 DWHYMC_id = DWHYMC_map[DWHYMC]
#                 DWHYMC_list.append(DWHYMC_id)
#
#         for DWXZMC in lines[2].split(":")[1].split(','):
#             if DWXZMC not in DWXZMC_map:
#                 DWXZMC_map.update({DWXZMC: DWXZMC_count})
#                 DWXZMC_list.append(DWXZMC_count)
#                 DWXZMC_count = DWXZMC_count + 1
#             else:
#                 DWXZMC_id = DWXZMC_map[DWXZMC]
#                 DWXZMC_list.append(DWXZMC_id)
#
#         for GZZWLBMC in lines[3].split(':')[1].split(','):
#             if GZZWLBMC not in GZZWLBMC_map:
#                 GZZWLBMC_map.update({GZZWLBMC: GZZWLBMC_count})
#                 GZZWLBMC_list.append(GZZWLBMC_count)
#                 GZZWLBMC_count = GZZWLBMC_count + 1
#             else:
#                 GZZWLBMC_id = GZZWLBMC_map[GZZWLBMC]
#                 GZZWLBMC_list.append(GZZWLBMC_id)
#
#         DWHYMC_list = ",".join(list(map(str, DWHYMC_list)))
#         DWXZMC_list = ",".join(list(map(str, DWXZMC_list)))
#         GZZWLBMC_list = ",".join(list(map(str, GZZWLBMC_list)))
#
#         output_line = work_id + '|' + DWHYMC_list + '|' + DWXZMC_list + '|' + GZZWLBMC_list + '\n'
#         fw_mapping.write(output_line)
#
#     return DWHYMC_count, DWXZMC_count, GZZWLBMC_count
#
#
# def print_statistic_info(genre_count, director_count, actor_count):
#     '''
#     print the number of genre, director and actor
#     '''
#
#     print('The number of genre is: ' + str(genre_count))
#     print('The number of director is: ' + str(director_count))
#     print('The number of actor is: ' + str(actor_count))
#
#
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description=''' Map Auxiliary Information into ID''')
#
#     parser.add_argument('--auxiliary', type=str, dest='auxiliary_file', default='data/xdu/auxiliary.txt')
#     parser.add_argument('--mapping', type=str, dest='mapping_file', default='data/xdu/auxiliary-mapping.txt')
#
#     parsed_args = parser.parse_args()
#
#     auxiliary_file = parsed_args.auxiliary_file
#     mapping_file = parsed_args.mapping_file
#
#     fr_auxiliary = open(auxiliary_file, 'r', encoding='utf-8')
#     fw_mapping = open(mapping_file, 'w')
#
#     DWHYMC_count, DWXZMC_count, GZZWLBMC_count = mapping(fr_auxiliary, fw_mapping)
#     print_statistic_info(DWHYMC_count, DWXZMC_count, GZZWLBMC_count)
#
#     fr_auxiliary.close()
#     fw_mapping.close()
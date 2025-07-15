# This is used to map the auxiliary information (genre, director and actor) into mapping ID for MovieLens

import argparse


def mapping(fr_auxiliary, fw_mapping):
    '''
    mapping the auxiliary info (e.g., genre, director, actor) into ID

    Inputs:
        @fr_auxiliary: the auxiliary infomation
        @fw_mapping: the auxiliary mapping information
    '''
    DEPARTMENT_map = {}
    MAJOR_map = {}
    ZYFX_map = {}
    # actor_map = {}
    # director_map = {}
    # genre_map = {}

    # actor_count = director_count = genre_count = 0
    DEPARTMENT_count = MAJOR_count = ZYFX_count = 0

    for line in fr_auxiliary:

        lines = line.replace('\n', '').split('|')
        if len(lines) != 4:
            continue

        # movie_id = lines[0].split(':')[1]
        SID = lines[0].split(':')[1]
        DEPARTMENT_list = []
        MAJOR_list = []
        ZYFX_list = []

        for DEPARTMENT in lines[1].split(":")[1].split(','):
            if DEPARTMENT not in DEPARTMENT_map:
                DEPARTMENT_map.update({DEPARTMENT: DEPARTMENT_count})
                DEPARTMENT_list.append(DEPARTMENT_count)
                DEPARTMENT_count = DEPARTMENT_count + 1
            else:
                DEPARTMENT_id = DEPARTMENT_map[DEPARTMENT]
                DEPARTMENT_list.append(DEPARTMENT_id)

        for MAJOR in lines[2].split(":")[1].split(','):
            if MAJOR not in MAJOR_map:
                MAJOR_map.update({MAJOR: MAJOR_count})
                MAJOR_list.append(MAJOR_count)
                MAJOR_count = MAJOR_count + 1
            else:
                MAJOR_id = MAJOR_map[MAJOR]
                MAJOR_list.append(MAJOR_id)

        for ZYFX in lines[3].split(':')[1].split(','):
            if ZYFX not in ZYFX_map:
                ZYFX_map.update({ZYFX: ZYFX_count})
                ZYFX_list.append(ZYFX_count)
                ZYFX_count = ZYFX_count + 1
            else:
                ZYFX_id = ZYFX_map[ZYFX]
                ZYFX_list.append(ZYFX_id)

        DEPARTMENT_list = ",".join(list(map(str, DEPARTMENT_list)))
        MAJOR_list = ",".join(list(map(str, MAJOR_list)))
        ZYFX_list = ",".join(list(map(str, ZYFX_list)))

        output_line = SID + '|' + DEPARTMENT_list + '|' + MAJOR_list + '|' + ZYFX_list + '\n'
        fw_mapping.write(output_line)

    return DEPARTMENT_count, MAJOR_count, ZYFX_count


def print_statistic_info(DEPARTMENT_count, MAJOR_count, ZYFX_count):
    '''
    print the number of genre, director and actor
    '''

    print('The number of DEPARTMENT is: ' + str(DEPARTMENT_count))
    print('The number of MAJOR is: ' + str(MAJOR_count))
    print('The number of ZYFX is: ' + str(ZYFX_count))

def main(auxiliary_file='data/xdu/auxiliary_com.txt', mapping_file='data/xdu/auxiliary-mapping-com.txt'):
    fr_auxiliary = open(auxiliary_file, 'r', encoding='utf-8')
    fw_mapping = open(mapping_file, 'w')

    DWHYMC_count, DWXZMC_count, GZZWLBMC_count = mapping(fr_auxiliary, fw_mapping)
    print_statistic_info(DWHYMC_count, DWXZMC_count, GZZWLBMC_count)

    fr_auxiliary.close()
    fw_mapping.close()
#
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description=''' Map Auxiliary Information into ID''')
#
#     parser.add_argument('--auxiliary', type=str, dest='auxiliary_file', default='data/xdu/auxiliary_com.txt')
#     parser.add_argument('--mapping', type=str, dest='mapping_file', default='data/xdu/auxiliary-mapping-com.txt')
#
#     parsed_args = parser.parse_args()
#
#     auxiliary_file = parsed_args.auxiliary_file
#     mapping_file = parsed_args.mapping_file
#
#     fr_auxiliary = open(auxiliary_file, 'r', encoding='utf-8')
#     fw_mapping = open(mapping_file, 'w')
#
#     DEPARTMENT_count, MAJOR_count, ZYFX_count = mapping(fr_auxiliary, fw_mapping)
#     print_statistic_info(DEPARTMENT_count, MAJOR_count, ZYFX_count)
#
#     fr_auxiliary.close()
#     fw_mapping.close()
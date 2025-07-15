import heapq
import numpy as np

class LSTMEvaluation(object):
	'''
	recurrent neural network evaluation
	'''
	def __init__(self, embedding_dict, all_movie, train_dict, test_dict):
		super(LSTMEvaluation, self).__init__()
		self.embedding_dict = embedding_dict
		self.all_movie = all_movie
		self.train_dict = train_dict
		self.test_dict = test_dict
		self.mrr = 0.0


	def calculate_ranking_score(self):
		'''
		calculate ranking score of unrated movies for each user
		'''
		score_dict = {}
		top_score_dict = {}

		for user in self.test_dict:
			if user in self.embedding_dict and user in self.train_dict:
				for movie in self.all_movie:
					if movie not in self.train_dict[user] and movie in self.embedding_dict:
						embedding_user = self.embedding_dict[user]
						embedding_movie = self.embedding_dict[movie]
						score = np.dot(embedding_user, embedding_movie)
						if user not in score_dict:
							score_dict.update({user:{movie:score}})  #
						else:
							score_dict[user].update({movie:score})

				#rank score in a descending order
				if user in score_dict and len(score_dict[user]) > 1:
					item_score_list = score_dict[user]
					k = min(len(item_score_list), 15) #to speed up the ranking process, we only find the top 15 movies
					top_item_list = heapq.nlargest(k, item_score_list, key=item_score_list.get)
					top_score_dict.update({user:top_item_list})  # top_item_list结构：{movie:score}

		return top_score_dict  #  蕴含推荐列表

	def calculate_results(self, top_score_dict, k):
		'''
		calculate the final results: pre@k and mrr
		'''
		precision = 0.0
		recall = 0.0  # 7_18
		isMrr = False
		if k == 10: isMrr = True

		user_size = 0
		mrr_5 = 0.0  # 新增：用于计算 mrr@5
		ndcg_5 = 0.0  # 新增：用于计算 ndcg@5
		for user in self.test_dict:
			if user in top_score_dict:
				user_size = user_size + 1
				candidate_item = top_score_dict[user]
				candidate_size = len(candidate_item)
				hit = 0
				min_len = min(candidate_size, k)
				dcg_5 = 0.0  # 新增：用于计算 dcg@5
				for i in range(min_len):
					if candidate_item[i] in self.test_dict[user]:
						hit = hit + 1
						##################################
						if i < 5:  # 仅在前5个推荐项中计算
							mrr_5 += float(1 / (i + 1))
							dcg_5 += 1 / np.log2(i + 2)  # DCG公式
                        ########################################
						if isMrr: self.mrr += float(1/(i+1))

				###########################
				if len(self.test_dict[user]) >= 5:
					ideal_dcg_5 = sum([1 / np.log2(i + 2) for i in range(5)])
				else:
					ideal_dcg_5 = sum([1 / np.log2(i + 2) for i in range(len(self.test_dict[user]))])

				ndcg_5 += dcg_5 / ideal_dcg_5  # 新增：计算 NDCG@5
				###########################
				hit_ratio = float(hit / min_len)
				recal_hit_ratio = float(hit / len(self.test_dict[user]))  # 7_18
				precision += hit_ratio
				recall += recal_hit_ratio  # 7_18

		precision = precision / user_size
		recall = recall / user_size  # 7_18
		print ('precision@' + str(k) + ' is: ' + str(precision))
		print('recall@' + str(k) + ' is: ' + str(recall))  # 7_18
		if isMrr:
			self.mrr = self.mrr / user_size
			print ('mrr@' + str(k) +' is: ' + str(self.mrr))
			#############################################
			mrr_5 = mrr_5 / user_size  # 新增：计算 mrr@5
			ndcg_5 = ndcg_5 / user_size  # 新增：计算 ndcg@5
			print('mrr@5 is: ' + str(mrr_5))  # 新增：输出 mrr@5
			print('ndcg@5 is: ' + str(ndcg_5))  # 新增：输出 ndcg@5
			###############################################

		return precision, self.mrr




	# def calculate_results(self, top_score_dict, k):
	# 	'''
    #     calculate the final results: pre@k and mrr
    #     '''
	# 	precision = 0.0
	# 	recall = 0.0  # 7_18
	# 	isMrr = False
	# 	if k == 10: isMrr = True
	#
	# 	user_size = 0
	# 	mrr_5 = 0.0  # 新增：用于计算 mrr@5
	# 	ndcg_5 = 0.0  # 新增：用于计算 ndcg@5
	#
	# 	for user in self.test_dict:
	# 		if user in top_score_dict:
	# 			user_size += 1
	# 			candidate_item = top_score_dict[user]
	# 			candidate_size = len(candidate_item)
	# 			hit = 0
	# 			min_len = min(candidate_size, k)
	# 			dcg_5 = 0.0  # 新增：用于计算 dcg@5
	#
	# 			for i in range(min_len):
	# 				if candidate_item[i] in self.test_dict[user]:
	# 					hit += 1
	# 					if i < 5:  # 仅在前5个推荐项中计算
	# 						mrr_5 += float(1 / (i + 1))
	# 						dcg_5 += 1 / np.log2(i + 2)  # DCG公式
	#
	# 					if isMrr:
	# 						self.mrr += float(1 / (i + 1))
	#
	# 			if len(self.test_dict[user]) >= 5:
	# 				ideal_dcg_5 = sum([1 / np.log2(i + 2) for i in range(5)])
	# 			else:
	# 				ideal_dcg_5 = sum([1 / np.log2(i + 2) for i in range(len(self.test_dict[user]))])
	#
	# 			ndcg_5 += dcg_5 / ideal_dcg_5  # 新增：计算 NDCG@5
	#
	# 			hit_ratio = float(hit / min_len)
	# 			recal_hit_ratio = float(hit / len(self.test_dict[user]))  # 7_18
	#
	# 			precision += hit_ratio
	# 			recall += recal_hit_ratio  # 7_18
	#
	# 	precision = precision / user_size
	# 	recall = recall / user_size  # 7_18
	# 	print('precision@' + str(k) + ' is: ' + str(precision))
	# 	print('recall@' + str(k) + ' is: ' + str(recall))  # 7_18
	# 	if isMrr:
	# 		self.mrr = self.mrr / user_size
	# 		mrr_5 = mrr_5 / user_size  # 新增：计算 mrr@5
	# 		ndcg_5 = ndcg_5 / user_size  # 新增：计算 ndcg@5
	# 		print('mrr@' + str(k) + ' is: ' + str(self.mrr))
	# 		print('mrr@5 is: ' + str(mrr_5))  # 新增：输出 mrr@5
	# 		print('ndcg@5 is: ' + str(ndcg_5))  # 新增：输出 ndcg@5
	#
	# 	return precision, self.mrr




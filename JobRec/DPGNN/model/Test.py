from JobRec.DPGNN.model.prediction import JobRecommender

if __name__ == "__main__":
    config_file = 'xdu'
    checkpoint_path = './saved/DPGNN-Sep-11-2024_00-09-16.pth'
    recommender = JobRecommender(config_file=config_file, checkpoint_path=checkpoint_path)
    while True:
        try:
            direction = input("请选择推荐方向（1：根据用户ID推荐工作，2：根据工作ID推荐用户）：")
            if direction == '1':
                user_id_input = input("请输入用户ID：")
                recommendations = recommender.recommend_jobs_for_user(user_id_input, num_recommendations=10)
                print("推荐的职位列表：")
                for job_id, score in recommendations:
                    print(f"职位ID: {job_id}, 评分: {score}")
            elif direction == '2':
                job_id_input = input("请输入工作ID：")
                recommendations = recommender.recommend_users_for_job(job_id_input, num_recommendations=10)
                print("推荐的用户列表：")
                for user_id, score in recommendations:
                    print(f"用户ID: {user_id}, 评分: {score}")
            else:
                print("请输入有效的选择（1或2）。")
        except ValueError:
            print("请输入有效的ID。")
        except KeyboardInterrupt:
            print("\n程序已终止。")
            break

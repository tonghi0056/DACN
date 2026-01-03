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
import csv
from datetime import datetime

# --- HÀM GHI FILE CSV (BENCHMARK) ---
def save_agent_benchmark(output_dir, env_type, algo, episodes, success_rate, avg_reward, duration):
    csv_file = os.path.join(output_dir, "agent_benchmark.csv")
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp', 'Mode', 'Algorithm', 'Episodes', 'Success Rate (%)', 'Avg Reward', 'Duration (s)'])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                env_type.upper(), algo.upper(), episodes,
                f"{success_rate:.2f}", f"{avg_reward:.2f}", f"{duration:.2f}"
            ])
        logging.info(f"\n[BENCHMARK] Saved to: {os.path.abspath(csv_file)}")
    except Exception as e:
        logging.error(f"CSV Error: {e}")

def run_training(config_path, model_save_path, model_load_path=None, env_type='training', algorithm='q_learning'):
    
    # --- SETUP PATHS & LOGGING ---
    output_dir = "results/train_results" if env_type == 'training' else "results/target_results"
    os.makedirs(output_dir, exist_ok=True)
    
    LOG_FILE = os.path.join(output_dir, f"{env_type}_log.txt") 
    root_logger = logging.getLogger()
    if root_logger.hasHandlers(): root_logger.handlers.clear()
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'), logging.StreamHandler()])
    
    start_time = time.time()
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    agent_cfg = config['Agent']
    train_cfg = config['Training']
    
    # --- INIT ENV ---
    try:
        env = TrainingEnvironment(config_path) if env_type == 'training' else TargetEnvironment(config_path)
    except Exception as e:
        logging.error(f"Env Init Error: {e}")
        return

    # --- INIT AGENT ---
    action_size = env.get_action_space_size()
    lr, gamma = float(agent_cfg.get('learning_rate', 0.1)), float(agent_cfg.get('discount_factor', 0.9))
    eps, eps_decay, eps_min = float(agent_cfg.get('epsilon', 1.0)), float(agent_cfg.get('epsilon_decay', 0.995)), float(agent_cfg.get('epsilon_min', 0.01))

    # [FIX] Thêm logic xử lý 'q_transfer'
    if algorithm == 'q_learning': 
        agent = QLearningAgent(action_size, lr, gamma, eps, eps_decay, eps_min)
    elif algorithm == 'q_transfer': 
        # q_transfer thực chất là Q-Learning load model cũ
        agent = QLearningAgent(action_size, lr, gamma, eps, eps_decay, eps_min)
    elif algorithm == 'sarsa': 
        agent = SarsaAgent(action_size, lr, gamma, eps, eps_decay, eps_min)
    elif algorithm == 'random': 
        agent = RandomAgent(action_space_size=action_size)
    else: 
        raise ValueError(f"Unknown algo: {algorithm}")
    
    if model_load_path and algorithm != 'random':
        try:
            agent.load_model(model_load_path)
            if env_type == 'target': 
                # Chế độ Target: Giảm Epsilon để dùng kiến thức đã học (Exploitation)
                agent.epsilon = 0.1 
                logging.info(f"TARGET MODE: Epsilon set to 0.1")
        except: logging.error(f"Model Load Error.")

    # --- TRAINING LOOP ---
    total_episodes = int(train_cfg['episodes'])
    max_steps = int(train_cfg['max_steps_per_episode'])
    rewards_per_episode, moving_avg_rewards, moving_avg_episodes = [], [], []
    total_successes = 0 
    log_freq = 10 if total_episodes <= 1000 else 100
    
    logging.info(f"--- Bắt đầu {total_episodes} episodes ({algorithm}) ---")

    try:
        for episode in range(total_episodes):
            state = env.reset()
            done = False
            episode_reward = 0
            action = agent.choose_action(state)

            for step in range(max_steps):
                next_state, reward, done = env.step(action)
                next_action = agent.choose_action(next_state)
                
                if algorithm == 'sarsa': agent.learn(state, action, reward, next_state, next_action)
                elif algorithm == 'q_learning' or algorithm == 'q_transfer': agent.learn(state, action, reward, next_state)
                
                state, action = next_state, next_action 
                episode_reward += reward
                
                # Logic đếm Success: Reward > 90 (Vì 100 thưởng - phạt)
                if done and reward > 90:
                    total_successes += 1
                    break 
                
                if done: break
            
            rewards_per_episode.append(episode_reward)
            agent.update_epsilon()

            if (episode + 1) % log_freq == 0:
                last_n = rewards_per_episode[-log_freq:] 
                avg_reward = sum(last_n) / len(last_n)
                moving_avg_rewards.append(avg_reward)
                moving_avg_episodes.append(episode + 1)
                logging.info(f"Ep {episode + 1}: Avg Reward: {avg_reward:.2f} | Successes: {total_successes}")

    except KeyboardInterrupt:
        logging.warning("User stopped.")
    
    # --- SAVE MODEL & PLOT ---
    if algorithm != 'random': agent.save_model(model_save_path)
    
    # Metrics
    end_time = time.time()
    total_duration = end_time - start_time
    success_rate = (total_successes / len(rewards_per_episode)) * 100 if rewards_per_episode else 0
    avg_reward_overall = sum(rewards_per_episode) / len(rewards_per_episode) if rewards_per_episode else 0
    
    # Stats Text Box
    last_10_percent = int(total_episodes * 0.9)
    avg_reward_last_10 = sum(rewards_per_episode[last_10_percent:]) / len(rewards_per_episode[last_10_percent:]) if rewards_per_episode[last_10_percent:] else 0
    
    stats_text = (f"Algorithm: {algorithm.upper()}\n"
                  f"Total Success: {total_successes}/{len(rewards_per_episode)} ({success_rate:.2f}%)\n"
                  f"Avg Reward (All): {avg_reward_overall:.2f}\n"
                  f"Avg Reward (Last 10%): {avg_reward_last_10:.2f}\n"
                  f"Time: {total_duration:.2f}s")
    
    logging.info("\n" + stats_text)
    save_agent_benchmark(output_dir, env_type, algorithm, len(rewards_per_episode), success_rate, avg_reward_overall, total_duration)

    if moving_avg_episodes:
        plt.figure(figsize=(10, 6))
        plt.plot(moving_avg_episodes, moving_avg_rewards, label='Avg Reward', linewidth=2)
        plt.title(f"Training Progress - {algorithm.upper()} ({env_type} mode)", fontsize=14)
        plt.xlabel("Episode")
        plt.ylabel("Average Reward")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.subplots_adjust(bottom=0.25)
        plt.figtext(0.95, 0.05, stats_text, ha="right", va="bottom", fontsize=10,
                    bbox={"boxstyle": "round,pad=0.5", "facecolor": "#f0f0f0", "edgecolor": "gray", "alpha": 0.9})
        plt.savefig(os.path.splitext(model_save_path)[0] + "_chart.png")

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
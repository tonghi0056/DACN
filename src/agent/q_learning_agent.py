import numpy as np
import random
from src.agent.q_table import QTable
import pickle

class QLearningAgent:
    """
    Hỗ trợ: Q-Learning, SARSA, và Random Agent.
    """
    # 1. Thêm tham số algorithm vào __init__
    def __init__(self, action_space_size, lr, gamma, epsilon, epsilon_decay, epsilon_min, algorithm='q_learning'):
        self.action_space_size = action_space_size
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.algorithm = algorithm.lower() # Lưu loại thuật toán: 'q_learning', 'sarsa', 'random'
        
        self.q_table = QTable(action_space_size)

    def choose_action(self, state):
        # 2. Logic cho Random Agent (Baseline)
        if self.algorithm == 'random':
            return random.randint(0, self.action_space_size - 1)

        # Logic Epsilon-Greedy (cho Q-Learning và SARSA)
        if random.uniform(0, 1) < self.epsilon:
            return random.randint(0, self.action_space_size - 1)
        else:
            state_key = self.q_table._get_state_key(state)
            if state_key not in self.q_table.q_table:
                return random.randint(0, self.action_space_size - 1)
            
            qs = self.q_table.q_table[state_key]
            max_val = max(qs)
            best_actions = [i for i, val in enumerate(qs) if val == max_val]
            return random.choice(best_actions)

    # 3. Cập nhật hàm learn để hỗ trợ SARSA (cần next_action)
    def learn(self, state, action, reward, next_state, next_action=None):
        if self.algorithm == 'random':
            return # Random Agent không cần học

        current_q = self.q_table.get_q_value(state, action)
        
        # --- KHÁC BIỆT CHÍNH Ở ĐÂY ---
        target_q = 0.0
        
        if self.algorithm == 'sarsa':
            # SARSA (On-Policy): Dựa vào hành động tiếp theo THỰC TẾ
            if next_action is None:
                # Fallback nếu code gọi thiếu, mặc định về max (như Q-Learning)
                target_q = self.q_table.get_max_q(next_state)
            else:
                target_q = self.q_table.get_q_value(next_state, next_action)
                
        else: 
            # Q-Learning (Off-Policy): Dựa vào hành động TỐT NHẤT tương lai (Max)
            target_q = self.q_table.get_max_q(next_state)
        # -----------------------------

        new_q = current_q + self.lr * (reward + self.gamma * target_q - current_q)
        self.q_table.update_q_value(state, action, new_q)

    def update_epsilon(self):
        # Random Agent không cần giảm epsilon
        if self.algorithm != 'random' and self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    # ... Các hàm save_model, load_model giữ nguyên ...
    def save_model(self, filepath):
        """Lưu Q-table xuống file dùng pickle"""
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.q_table, f)
            print(f"[Agent] Đã lưu model vào: {filepath}")
        except Exception as e:
            print(f"[Agent] Lỗi khi lưu model: {e}")

    def load_model(self, filepath):
        """Load Q-table từ file dùng pickle"""
        try:
            with open(filepath, 'rb') as f:
                self.q_table = pickle.load(f)
            print(f"[Agent] Đã tải model từ: {filepath}")
        except Exception as e:
            print(f"[Agent] Lỗi khi tải model: {e}")
import random
import pickle
from src.agent.q_table import QTable

class BaseAgent:
    def __init__(self, action_space_size, lr, gamma, epsilon, epsilon_decay, epsilon_min):
        self.action_space_size = action_space_size
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        self.q_table = QTable(action_space_size)

    def choose_action(self, state):
        # Logic Epsilon-Greedy chung cho các Agent có học
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

    def update_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_model(self, filepath):
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.q_table, f)
            print(f"[Agent] Đã lưu model vào: {filepath}")
        except Exception as e:
            print(f"[Agent] Lỗi lưu model: {e}")

    def load_model(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                self.q_table = pickle.load(f)
            print(f"[Agent] Đã tải model từ: {filepath}")
        except Exception as e:
            print(f"[Agent] Lỗi tải model: {e}")
            
    # Hàm learn sẽ để trống để các con tự viết
    def learn(self, *args, **kwargs):
        raise NotImplementedError("Class con phải tự định nghĩa hàm learn")
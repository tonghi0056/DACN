import random

class RandomAgent:
    # Random Agent không cần nhiều tham số phức tạp
    def __init__(self, action_space_size):
        self.action_space_size = action_space_size
        # Giữ lại mấy hàm này cho đồng bộ interface với main.py, dù không dùng
        self.epsilon = 0 

    def choose_action(self, state):
        return random.randint(0, self.action_space_size - 1)

    def learn(self, state, action, reward, next_state, next_action=None):
        pass # Random không học gì cả

    def update_epsilon(self):
        pass

    def save_model(self, filepath):
        print("[Random] Random agent không cần lưu model.")

    def load_model(self, filepath):
        print("[Random] Random agent không có model để load.")
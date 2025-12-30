from src.agent.base_agent import BaseAgent

class QLearningAgent(BaseAgent):
    def learn(self, state, action, reward, next_state, next_action=None):
        # Q-Learning: Off-Policy (Dùng max Q của next_state)
        current_q = self.q_table.get_q_value(state, action)
        max_next_q = self.q_table.get_max_q(next_state)
        
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table.update_q_value(state, action, new_q)
from src.agent.base_agent import BaseAgent

class SarsaAgent(BaseAgent):
    def learn(self, state, action, reward, next_state, next_action=None):
        # SARSA: On-Policy (Dùng Q của next_action thực tế)
        if next_action is None:
            return # SARSA bắt buộc phải biết next_action
            
        current_q = self.q_table.get_q_value(state, action)
        next_q = self.q_table.get_q_value(next_state, next_action)
        
        new_q = current_q + self.lr * (reward + self.gamma * next_q - current_q)
        self.q_table.update_q_value(state, action, new_q)
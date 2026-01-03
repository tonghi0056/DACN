import numpy as np

class StateManager:
    def __init__(self):
        # --- FIX: Khai báo biến này TRƯỚC khi gọi reset_state() ---
        self.target_index = 0.0 
        
        self.reset_state()

    def set_target_mission(self, index, total_targets):
        # Normalize target ID về khoảng [0, 1]
        # Tránh chia cho 0 nếu chỉ có 1 target
        denom = max(1, total_targets - 1)
        self.target_index = index / denom

    def reset_state(self):
        self.current_state = ""
        # 0: Start, 1: Union, 2: Select, 3: Collecting Cols, 4: From, 5: End
        self.phase = 0.0 
        self.collected_count = 0.0
        # self.last_action_type = 0.0 # (Có thể bỏ nếu không dùng trong vector)
        
        return self.get_feature_vector()

    def update_state(self, action_string, action_index, phase_info=None):
        # Cập nhật chuỗi payload hiển thị
        clean_act = action_string.strip()
        
        # Logic ghép chuỗi thông minh hơn xíu để không bị dính chùm
        if clean_act == "," or clean_act.startswith("--") or clean_act.startswith(")"):
            self.current_state += clean_act
        else:
            if self.current_state == "" or self.current_state.endswith(" "):
                self.current_state += clean_act
            else:
                self.current_state += " " + clean_act
        
        # Cập nhật thông tin từ RewardSystem gửi sang (Phase & Progress)
        if phase_info:
            self.phase = float(phase_info.get('phase', 0))
            # Normalize tiến độ lấy cột (ví dụ lấy đc 3/5 cột -> 0.6)
            self.collected_count = float(phase_info.get('progress', 0.0))
            
        return self.get_feature_vector()

    def get_feature_vector(self):
        # Vector cực kỳ cô đọng giúp AI học nhanh:
        # [Mục tiêu là ai?, Đang ở bước nào?, Đã lấy đc bao nhiêu %?]
        # Đảm bảo trả về tuple số thực (float) để không lỗi tính toán
        return tuple([
            float(self.target_index),       # Target ID (Quan trọng nhất)
            float(self.phase) / 5.0,        # Phase (0.0 -> 1.0)
            float(self.collected_count),    # Progress (0.0 -> 1.0)
        ])
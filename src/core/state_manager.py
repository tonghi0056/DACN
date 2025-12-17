import numpy as np

class StateManager:
    def __init__(self):
        self.current_state = ""
        self.flags = {
            "is_last_start": 0.0,
            "is_last_union": 0.0,
            "is_last_select": 0.0,
            "is_last_column": 0.0,
            "is_last_comma": 0.0,
            "is_last_null": 0.0,
            "is_last_from": 0.0,
            "is_last_end": 0.0
        }

    def reset_state(self):
        self.current_state = ""
        for k in self.flags: self.flags[k] = 0.0
        return self.get_feature_vector()

    def update_state(self, action_string, action_index):
        # 1. Cập nhật chuỗi (Giữ nguyên logic cũ)
        s_action = action_string.upper().strip()
        
        if action_string.strip() == "," or action_string.startswith("--") or action_string.startswith(")"):
            self.current_state += action_string.strip()
        else:
            if self.current_state == "" or self.current_state.endswith(" "):
                self.current_state += action_string
            else:
                self.current_state += " " + action_string

        # 2. Reset flags
        for k in self.flags: self.flags[k] = 0.0

        # 3. Bật cờ (State Identification)
        if "A'))" in s_action: self.flags["is_last_start"] = 1.0
        elif "UNION" in s_action: self.flags["is_last_union"] = 1.0
        elif "SELECT" in s_action: self.flags["is_last_select"] = 1.0
        elif s_action in ["ID", "EMAIL", "PASSWORD"]: self.flags["is_last_column"] = 1.0
        elif "," in s_action and "NULL" not in s_action: self.flags["is_last_comma"] = 1.0
        elif "NULL" in s_action: self.flags["is_last_null"] = 1.0
        elif "FROM" in s_action: self.flags["is_last_from"] = 1.0
        elif "--" in s_action: self.flags["is_last_end"] = 1.0

        return self.get_feature_vector()

    def get_feature_vector(self):
        s = self.current_state.upper()
        
        # --- TÍNH NĂNG MỚI: ĐẾM SỐ CỘT (QUAN TRỌNG) ---
        # Đếm xem từ sau SELECT đến giờ có bao nhiêu dấu phẩy rồi -> Ước lượng số cột
        # Logic: Số cột ~ Số dấu phẩy + 1 (trong đoạn SELECT...FROM)
        select_index = s.rfind("SELECT")
        from_index = s.rfind("FROM")
        
        items_count = 0
        if select_index != -1:
            segment = s[select_index:] if from_index == -1 else s[select_index:from_index]
            # Đếm số lượng dấu phẩy để biết độ dài hiện tại
            items_count = segment.count(",") 
            
        # Chuẩn hóa (giả sử max cột là 10)
        col_density = min(items_count / 10.0, 1.0)
        
        # Kiểm tra sự hiện diện của bộ 3 nguyên tử
        has_id = 1.0 if "ID" in s else 0.0
        has_email = 1.0 if "EMAIL" in s else 0.0
        has_pass = 1.0 if "PASSWORD" in s else 0.0
        
        # Global Features
        length_norm = min(len(s) / 150.0, 1.0)
        context_vector = list(self.flags.values()) 

        # Vector output: Thêm col_density và 3 biến check column
        return tuple([col_density, has_id, has_email, has_pass, length_norm] + context_vector)
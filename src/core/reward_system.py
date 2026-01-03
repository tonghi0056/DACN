# FILE: src/core/reward_system.py

class RewardSystem:
    def __init__(self, normal_count, success_marker, error_marker, env_type='training'):
        self.env_type = env_type
        self.collected_columns = []
        self.current_target_table = None
        
        # Định nghĩa các giai đoạn (Phases)
        self.PHASE_START = 0
        self.PHASE_UNION = 1
        self.PHASE_SELECT = 2
        self.PHASE_COLLECT = 3
        self.PHASE_FROM = 4
        self.PHASE_END = 5
        
        self.current_phase = self.PHASE_START
        
        # TARGET MAP (Danh sách bảng và cột mục tiêu)
        self.TARGET_MAP = {
            "sqlite_master": ["type", "name", "tbl_name", "sql"],
            "Users": ["id", "email", "password", "role", "totpSecret", "deluxeToken"],
            "SecurityAnswers": ["UserId", "answer", "SecurityQuestionId"],
            "Addresses": ["fullName", "mobileNum", "zipCode", "streetAddress", "city", "state", "country"],
            "Cards": ["fullName", "cardNum", "expMonth", "expYear", "UserId"],
            "Challenges": ["name", "key", "description", "solved", "category", "difficulty"],
            "BasketItems": ["BasketId", "ProductId", "quantity"],
            "Baskets": ["id", "coupon", "UserId"],
            "Captchas": ["captchaId", "captcha", "answer"],
            "Complaints": ["message", "file", "UserId"],
            "Deliveries": ["name", "price", "eta", "icon"],
            "Feedbacks": ["comment", "rating", "UserId"],
            "ImageCaptchas": ["image", "answer", "UserId"],
            "Memories": ["caption", "imagePath", "UserId"],
            "PrivacyRequests": ["deletionRequested", "UserId"],
            "Quantities": ["ProductId", "quantity", "limitPerUser"],
            "Recycles": ["quantity", "isPickup", "date", "UserId"],
            "SecurityQuestions": ["question", "id"],
            "Wallets": ["balance", "UserId"],
            "Products": ["name", "price", "image", "description"]
        }

    def set_target(self, table_name):
        self.current_target_table = table_name
        self.collected_columns = []
        self.current_phase = self.PHASE_START

    def get_phase_info(self):
        # Tính % hoàn thành cột để gửi cho State Manager
        required = self.TARGET_MAP.get(self.current_target_table, [])
        progress = len(self.collected_columns) / len(required) if required else 0.0
        return {'phase': self.current_phase, 'progress': min(progress, 1.0)}

    def calculate_reward(self, response, payload_fragment):
        # act là từ khóa hành động vừa chọn (ví dụ: "SELECT", "email", ...)
        act = payload_fragment.strip().upper()
        
        reward = -1.0 # Phạt nhẹ mỗi bước để khuyến khích hoàn thành sớm
        done = False
        
        # --- LOGIC MÁY TRẠNG THÁI (STATE MACHINE) ---
        
        # 1. Giai đoạn START: Bắt buộc bắt đầu bằng a'))
        if self.current_phase == self.PHASE_START:
            if "A'))" in act:
                reward += 10.0
                self.current_phase = self.PHASE_UNION
            elif act in ["UNION", "SELECT", "FROM"]:
                reward -= 10.0 # Phạt nặng nếu nhảy cóc

        # 2. Giai đoạn UNION: Cần từ khóa UNION
        elif self.current_phase == self.PHASE_UNION:
            if "UNION" in act:
                reward += 15.0
                self.current_phase = self.PHASE_SELECT
            elif "SELECT" in act: 
                reward -= 10.0
                
        # 3. Giai đoạn SELECT: Cần từ khóa SELECT
        elif self.current_phase == self.PHASE_SELECT:
            if "SELECT" in act:
                reward += 15.0
                self.current_phase = self.PHASE_COLLECT
            elif "FROM" in act:
                reward -= 20.0
                
        # 4. Giai đoạn COLLECT: Thu thập cột
        elif self.current_phase == self.PHASE_COLLECT:
            target_cols = [x.upper() for x in self.TARGET_MAP.get(self.current_target_table, [])]
            
            # Nếu chọn đúng cột mục tiêu
            if act in target_cols:
                if act not in self.collected_columns:
                    reward += 30.0 # Thưởng ĐẬM cho cột mới
                    self.collected_columns.append(act)
                else:
                    reward -= 5.0 # Phạt nhẹ nếu lặp lại cột đã lấy
            
            # Nếu chọn cột rác (của bảng khác)
            elif any(act in [x.upper() for x in v] for v in self.TARGET_MAP.values()):
                reward -= 15.0 # Phạt vì chọn sai cột
            
            # Nếu dùng NULL (Tốt, để lấp đầy số lượng cột)
            elif "NULL" in act:
                reward += 2.0
            
            # Dấu phẩy (Cần thiết để ngăn cách)
            elif "," in act:
                reward += 1.0
                
            # Chuyển sang giai đoạn FROM
            elif "FROM" in act:
                # Chỉ cho phép sang FROM nếu đã lấy đc ít nhất 1 cột
                if len(self.collected_columns) > 0:
                    reward += 20.0
                    self.current_phase = self.PHASE_FROM
                else:
                    reward -= 20.0 # Chưa lấy gì mà đòi FROM
        
        # 5. Giai đoạn FROM: Chọn bảng đúng
        elif self.current_phase == self.PHASE_FROM:
            # act ở đây ví dụ là " FROM Users"
            # Cắt chữ FROM đi để lấy tên bảng
            chosen_table = act.replace("FROM", "").strip()
            
            if chosen_table.upper() == self.current_target_table.upper():
                reward += 100.0 # <--- ĐÃ SỬA: Thưởng 100 điểm để main.py đếm success chuẩn xác
                self.current_phase = self.PHASE_END
                done = True # HOÀN THÀNH NHIỆM VỤ
            elif "FROM" in act: # Chọn sai bảng
                reward -= 50.0 
                done = True # Thất bại, kết thúc luôn
            else:
                reward -= 5.0 # Chọn linh tinh ở bước cuối

        # [QUAN TRỌNG] Dòng return này phải nằm ngoài cùng, KHÔNG được thụt vào trong if/elif
        return reward, done
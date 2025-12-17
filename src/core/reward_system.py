class RewardSystem:
    def __init__(self, normal_count, success_marker, error_marker, env_type='training'):
        self.success_marker = success_marker
        self.last_action_keyword = None 
        
        # Danh sách từ khóa CẤU TRÚC (Chỉ được dùng 1 lần)
        self.structural_keywords = ["A'))", "UNION", "SELECT", "FROM", "USERS", "--"]
        
        # Danh sách CỘT QUAN TRỌNG
        self.unique_data_columns = ["ID", "EMAIL", "PASSWORD"]
        
        self.used_keywords = set()

    def reset(self):
        self.last_action_keyword = None
        self.used_keywords = set()

    def calculate_reward(self, response, payload):
        reward = 0.0
        done = False
        p_upper = payload.upper()
        current_kw = self._extract_last_keyword(payload)
        
        # --- 1. LUẬT TỬ HÌNH: CẤM SPAM TỪ KHÓA ---
        if current_kw in self.structural_keywords:
            if current_kw in self.used_keywords: return -10.0, True 
            self.used_keywords.add(current_kw)

        if current_kw in self.unique_data_columns:
            if current_kw in self.used_keywords: return -10.0, True
            self.used_keywords.add(current_kw)
            
        # Luật cấm spam NULL quá đà
        if p_upper.count("NULL") > 6:
            return -10.0, True

        # --- 2. LOGIC DI CHUYỂN (State Machine) ---
        if self.last_action_keyword is None:
            if "A'))" in current_kw: reward += 2.0 
            else: return -10.0, True 
        
        else:
            prev = self.last_action_keyword
            
            # [Giai đoạn 1: Khung sườn]
            if "A'))" in prev and "UNION" in current_kw: reward += 3.0
            elif "UNION" in prev and "SELECT" in current_kw: reward += 3.0
            
            # [Giai đoạn 2: CHỌN MÓN ĂN - CÓ THỨ TỰ]
            elif ("SELECT" in prev or "," in prev):
                
                # --- QUY ĐỊNH THỨ TỰ NGHIÊM NGẶT ---
                if current_kw in self.unique_data_columns:
                    # Cấm quay xe nếu đã có NULL
                    if "NULL" in self.used_keywords: return -10.0, True
                    
                    # 1. BẮT BUỘC ID ĐẦU TIÊN
                    if current_kw == "ID":
                        # ID luôn được chào đón đầu tiên
                        reward += 5.0
                        
                    # 2. EMAIL CHỈ ĐƯỢC CHỌN NẾU ĐÃ CÓ ID
                    elif current_kw == "EMAIL":
                        if "ID" in self.used_keywords: reward += 5.0
                        else: return -10.0, True # Chưa có ID mà chọn EMAIL -> CHẾT
                        
                    # 3. PASSWORD CHỈ ĐƯỢC CHỌN NẾU ĐÃ CÓ EMAIL
                    elif current_kw == "PASSWORD":
                        if "EMAIL" in self.used_keywords: reward += 5.0
                        else: return -10.0, True # Chưa có EMAIL mà chọn PASS -> CHẾT

                elif "NULL" in current_kw:
                    # NULL chỉ được chọn nếu đã lấy đủ 3 cột quan trọng (Hoặc chấp nhận mất điểm để lấp đầy)
                    # Ở đây ta cho phép NULL lấp đầy, nhưng thưởng thấp
                    reward += 1.0 

            # [Giai đoạn 3: Dấu phẩy]
            elif (prev in self.unique_data_columns or prev == "NULL") and current_kw == ",":
                reward += 2.0
                
            # [CHẶN LỖI CÚ PHÁP]
            elif prev == "," and current_kw == ",": return -10.0, True 
            elif (prev in self.unique_data_columns or prev == "NULL") and (current_kw in self.unique_data_columns or current_kw == "NULL"):
                return -10.0, True

            # [Giai đoạn 4: VỀ ĐÍCH]
            elif current_kw == "FROM":
                extracted_cols = [c for c in self.unique_data_columns if c in self.used_keywords]
                if len(extracted_cols) == 3:
                    reward += 50.0 
                elif "SELECT" in self.used_keywords:
                    reward -= 5.0
                else:
                    return -10.0, True 

            elif current_kw == "USERS":
                if "FROM" in self.used_keywords: reward += 5.0
                else: return -10.0, True

            elif current_kw == "--":
                if "USERS" in self.used_keywords: 
                #     reward += 20.0 
                #     done = True # <--- QUAN TRỌNG: CẮT ĐUÔI NGAY LẬP TỨC
                # else: return -10.0, True
            # Kiểm tra xem đã lấy đủ hàng nóng chưa
                    extracted_cols = [c for c in self.unique_data_columns if c in self.used_keywords]
                    
                    if len(extracted_cols) == 3:
                        # NẾU ĐÃ CÓ ĐỦ ID, EMAIL, PASSWORD MÀ CÒN CHỐT HẠ BẰNG "--"
                        # => COI NHƯ LÀ CHIẾN THẮNG TUYỆT ĐỐI (SUCCESS)
                        return 100.0, True 
                    else:
                        # Nếu chưa đủ hàng mà đòi chốt -> Phạt nhẹ hoặc thưởng ít
                        reward += 20.0
                        done = True
                    
                    # --------------------
                else: return -10.0, True

        # --- 3. WIN CHECK ---
        if str(self.success_marker) in str(response.text):
            return 100.0, True
            
        if "SQLITE_ERROR" in str(response.text):
            if "SELECTs to the left and right of UNION" in str(response.text):
                reward -= 0.5 
            else:
                reward -= 1.0 

        self.last_action_keyword = current_kw
        if len(payload) > 250: return -10.0, True
            
        return reward, done

    def _extract_last_keyword(self, payload):
        s = payload.upper().strip()
        # Ưu tiên check các ký tự đặc biệt ở cuối trước
        if s.endswith("--"): return "--"
        if s.endswith("A'))"): return "A'))" # <--- SỬA LỖI Ở ĐÂY (Bỏ check len < 6)
        
        if s.endswith("USERS"): return "USERS"
        if s.endswith("FROM"): return "FROM"
        if s.endswith("NULL"): return "NULL"
        if s.endswith(","): return ","
        if s.endswith("PASSWORD"): return "PASSWORD"
        if s.endswith("EMAIL"): return "EMAIL"
        if s.endswith("ID"): return "ID"
        if s.endswith("SELECT"): return "SELECT"
        if s.endswith("UNION"): return "UNION"
        
        # Fallback cho trường hợp khởi đầu ngắn
        if "A'))" in s and len(s) < 10: return "A'))"
        
        return "UNKNOWN"
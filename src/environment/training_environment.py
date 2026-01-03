import sqlite3
import configparser
import sys
import os
import random
import json
from src.environment.base_environment import BaseEnvironment
from src.core.action_space import ActionSpace
from src.core.reward_system import RewardSystem
from src.core.state_manager import StateManager

class TrainingEnvironment(BaseEnvironment):
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.success_marker = "admin@juice-sh.op"
        self.error_marker = "SQLITE_ERROR" 
        
        self.action_space = ActionSpace()
        self.state_manager = StateManager()
        self.reward_system = RewardSystem(0, self.success_marker, self.error_marker, 'training')
        
        # --- BẢNG CỬU CHƯƠNG (Copy y hệt từ Target để đồng bộ logic) ---
        # Dù Training không gửi request, nhưng ta dùng map này để validation
        self.TARGET_DATA = {
            "SCHEMA": { "cols": ["type", "name", "tbl_name", "sql"] },
            "USERS": { "cols": ["id", "email", "password", "role", "totpSecret", "lastLoginIp", "isActive", "deluxeToken"] },
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

        # --- DANH SÁCH BẢNG (PHẢI GIỐNG HỆT TARGET 100%) ---
        self.ORDERED_TABLES = [
            "sqlite_master", "Users", "SecurityQuestions", "SecurityAnswers", 
            "Feedbacks", "Complaints", "Addresses", "Cards", 
            "Wallets", "Products", "Baskets", "BasketItems", 
            "Challenges", "Memories", "Recycles", "Deliveries", 
            "Captchas", "ImageCaptchas", "PrivacyRequests", "Quantities"
        ]
        self.current_target_idx = 0

    def reset(self):
        self.state_manager.reset_state()
        self.current_target_idx = random.randint(0, len(self.ORDERED_TABLES) - 1)
        target_name = self.ORDERED_TABLES[self.current_target_idx]
        self.reward_system.set_target(target_name)
        self.state_manager.set_target_mission(self.current_target_idx, len(self.ORDERED_TABLES))
        return self.state_manager.get_feature_vector()

    def step(self, action_index):
        action_string = self.action_space.get_action_string(action_index)
        
        fake_response = None
        reward, done = self.reward_system.calculate_reward(fake_response, action_string)
        if "--" in action_string: done = True

        phase_info = self.reward_system.get_phase_info()
        self.state_manager.set_target_mission(self.current_target_idx, len(self.ORDERED_TABLES))
        new_state = self.state_manager.update_state(action_string, action_index, phase_info)
        
        # LOGIC "EASY MODE" CHO TRAINING
        if done:
            base_payload = self.state_manager.current_state
            
            # Chỉ cần Agent có ý định chọn bảng (có chữ FROM)
            if " FROM " in base_payload:
                # Coi như Agent ĐÃ CHỌN ĐÚNG bảng (vì Target Env sẽ tự sửa)
                reward = 100.0 
            else:
                reward = -50.0 # Phạt nếu không có FROM

        return new_state, reward, done

    def get_action_space_size(self):
        return self.action_space.get_action_space_size()
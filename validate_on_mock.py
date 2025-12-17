# validate_on_mock.py
import configparser
import logging
import argparse
import os
import sys

# --- Import các class từ source code ---
# Đảm bảo cấu trúc thư mục đúng: src/environment/training_environment.py
from src.environment.training_environment import TrainingEnvironment
from src.agent.q_learning_agent import QLearningAgent

def run_validation(config_path, model_path, attempts):
    """
    Chạy model đã train trên MÔI TRƯỜNG MOCK để xem payload sinh ra là gì.
    """
    
    # --- 1. Cài đặt Logging ---
    output_dir = "results/train_results"
    os.makedirs(output_dir, exist_ok=True)
    LOG_FILE = os.path.join(output_dir, "validate_log.txt")

    # Reset logger
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(message)s',
                        handlers=[logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'), 
                                  logging.StreamHandler()])
    
    logging.info(f"--- BẮT ĐẦU KIỂM TRA MODEL TRÊN MOCK ENV ---")

    # [QUAN TRỌNG] Kiểm tra file model có tồn tại không
    if not os.path.exists(model_path):
        logging.error(f"❌ LỖI: Không tìm thấy file model tại: '{model_path}'")
        logging.error("Vui lòng kiểm tra lại đường dẫn file .pkl trong thư mục results/")
        return

    logging.info(f"Config: {config_path}")
    logging.info(f"Model: {model_path}")

    # --- 2. Khởi tạo Môi trường & Agent ---
    try:
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        # Lấy tham số max_steps
        if 'Training' in config:
            max_steps = int(config['Training'].get('max_steps_per_episode', 50))
        else:
            max_steps = 50 # Giá trị mặc định nếu config lỗi
            
        # Khởi tạo Môi trường Mock
        env = TrainingEnvironment(config_path)
        
        # Khởi tạo Agent (Chế độ test: learning_rate=0, epsilon=0)
        # Epsilon = 0 để Agent luôn chọn hành động tối ưu nhất (Exploitation)
        agent = QLearningAgent(
            action_space_size=env.get_action_space_size(),
            lr=0.0,
            gamma=0.0,
            epsilon=0.0,
            epsilon_decay=0.0,
            epsilon_min=0.0
        )
        
        # Load Q-Table
        agent.load_model(model_path)
        
        logging.info("--> Đã load Model và Environment thành công.")
        
    except Exception as e:
        logging.error(f"Lỗi khởi tạo (Config/Env/Agent): {e}")
        return

    # --- 3. Chạy thử nghiệm (Validation Loop) ---
    success_count = 0
    
    for attempt in range(attempts):
        logging.info(f"\n--- [Lần thử {attempt + 1}/{attempts}] ---")
        
        state = env.reset()
        done = False
        step_count = 0
        current_payload = ""
        
        for step in range(max_steps):
            # Chọn hành động
            action = agent.choose_action(state)
            
            # Thực thi hành động
            next_state, reward, done = env.step(action)
            state = next_state
            step_count += 1
            
            # --- [SỬA LỖI Ở ĐÂY] ---
            # Lấy chuỗi Payload trực tiếp từ biến current_state
            if hasattr(env, 'state_manager'):
                current_payload = env.state_manager.current_state
            else:
                current_payload = "Error: env.state_manager not found"

            # In ra payload nếu thành công
            if reward >= 100: 
                logging.info(f"!!! 🏆 CHIẾN THẮNG (REAL) TẠI BƯỚC {step_count} !!!")
                logging.info(f"==> PAYLOAD: {current_payload}")
                logging.info(f"==> Reward: {reward}")
                success_count += 1
                break
                
            elif done:
                logging.info(f"💀 GAME OVER (Do vi phạm luật) tại bước {step_count}")
                logging.info(f"==> Payload chết: {current_payload}")
                logging.info(f"==> Reward: {reward}")
                break
        
        if not done and reward <= 50:
            logging.info(f"Thất bại sau {max_steps} bước.")
            logging.info(f"Payload cuối cùng: {current_payload}")

    # --- 4. Tổng kết ---
    logging.info(f"\n========================================")
    logging.info(f"TỔNG KẾT: Thắng {success_count}/{attempts} lần.")
    if success_count > 0:
        logging.info("HƯỚNG DẪN: Hãy copy 'PAYLOAD CHIẾN THẮNG' ở trên và thử nhập tay vào Web Target.")
        logging.info("1. Nếu Web Target lỗi SQL -> Model tốt, nhưng code TargetEnvironment chưa bắt được lỗi đó.")
        logging.info("2. Nếu Web Target chặn -> Model học được cách bypass Mock, nhưng Mock quá dễ so với WAF thật.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Soi payload của model trên môi trường giả lập.")
    
    parser.add_argument('--config', type=str, default="config/config_training.ini", help="File config")
    parser.add_argument('--model', type=str, required=True, help="Đường dẫn file .pkl model (VD: results/train_results/final_model.pkl)")
    parser.add_argument('--attempts', type=int, default=3, help="Số lần chạy thử")

    args = parser.parse_args()

    run_validation(args.config, args.model, args.attempts)
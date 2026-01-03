import matplotlib.pyplot as plt
import json
import os
import csv
import numpy as np

# --- CẤU HÌNH ĐƯỜNG DẪN ---
TRAIN_DIR = "results/train_results"
TARGET_DIR = "results/target_results"

# File nguồn
FILES = {
    # JSON chỉ dùng để vẽ đường cong học (Training Trend)
    "TRAIN_QL": os.path.join(TRAIN_DIR, "q_learning_trained_metrics.json"),
    "TRAIN_SARSA": os.path.join(TRAIN_DIR, "sarsa_trained_metrics.json"),
    
    # CSV DUY NHẤT để lấy thời gian chạy
    "CSV_BENCHMARK": os.path.join(TARGET_DIR, "agent_benchmark.csv")
}

def load_json(filepath):
    if not os.path.exists(filepath): return {}
    with open(filepath, 'r') as f: return json.load(f)

def get_smooth_data(episodes, rewards, window_size=100):
    """Làm mượt dữ liệu Training"""
    if not episodes or not rewards or len(rewards) < window_size:
        return episodes, rewards
    
    window = np.ones(window_size) / window_size
    y_smooth = np.convolve(rewards, window, mode='valid')
    x_smooth = episodes[len(episodes) - len(y_smooth):]
    return x_smooth, y_smooth

def get_time_from_single_csv(filepath, algo_keyword):
    """
    Chỉ đọc file agent_benchmark.csv.
    Tìm dòng mới nhất có chứa từ khóa algo_keyword trong cột Algorithm.
    """
    if not os.path.exists(filepath):
        print(f"[-] Không tìm thấy file CSV: {filepath}")
        return 0.0
    
    found_duration = 0.0
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Duyệt ngược từ dưới lên để lấy kết quả chạy mới nhất
            for row in reversed(list(reader)):
                algo = row.get('Algorithm', '').upper()
                
                # Tìm từ khóa (VD: SARSA, Q_LEARNING, TRANSFER)
                if algo_keyword in algo:
                    # Ưu tiên cột 'Duration (s)', nếu không có thì thử 'Total Time (s)'
                    val = row.get('Duration (s)', row.get('Total Time (s)', '0'))
                    found_duration = float(val)
                    break 
    except Exception as e:
        print(f"[-] Lỗi đọc CSV: {e}")
        
    return found_duration

# --- 1. VẼ BIỂU ĐỒ TRAINING ---
def plot_training_trend():
    print("--- [1] Vẽ biểu đồ Training (Từ JSON) ---")
    d_ql = load_json(FILES["TRAIN_QL"])
    d_sarsa = load_json(FILES["TRAIN_SARSA"])
    
    plt.figure(figsize=(10, 6))
    
    if d_ql:
        x, y = get_smooth_data(d_ql.get('episodes'), d_ql.get('rewards'), window_size=100)
        plt.plot(x, y, label="Q-Learning", color="#d32f2f", linewidth=3)
        
    if d_sarsa:
        x, y = get_smooth_data(d_sarsa.get('episodes'), d_sarsa.get('rewards'), window_size=100)
        plt.plot(x, y, label="SARSA", color="#1976d2", linestyle="--", linewidth=3)
        
    plt.title("Training Performance: Q-Learning vs SARSA", fontsize=14, fontweight='bold')
    plt.xlabel("Episodes")
    plt.ylabel("Average Reward")
    plt.legend(fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(TARGET_DIR, "1_training_trend.png"), dpi=300)
    print("    -> Đã lưu: 1_training_trend.png")
    plt.close()

# --- 2. VẼ BIỂU ĐỒ THỜI GIAN (CHỈ DÙNG AGENT_BENCHMARK.CSV) ---
def plot_time_comparison():
    print("--- [2] Vẽ biểu đồ Thời gian (Chỉ từ agent_benchmark.csv) ---")
    
    csv_file = FILES["CSV_BENCHMARK"]
    
    # 1. Q-Learning
    t_ql = get_time_from_single_csv(csv_file, "Q_LEARNING")
    
    # 2. SARSA
    t_sarsa = get_time_from_single_csv(csv_file, "SARSA")
    
    # 3. Q+Transfer (Tìm từ khóa TRANSFER hoặc Q_TRANSFER)
    t_transfer = get_time_from_single_csv(csv_file, "TRANSFER")
    # Phòng hờ nếu bạn lưu tên là GOD_MODE
    if t_transfer == 0: 
        t_transfer = get_time_from_single_csv(csv_file, "GOD")

    times = {
        "Q-Learning": t_ql,
        "SARSA": t_sarsa,
        "Q+Transfer": t_transfer
    }
    
    # Lọc bỏ giá trị 0
    times = {k: v for k, v in times.items() if v > 0}
    
    if not times:
        print("[-] Không tìm thấy dữ liệu thời gian trong file agent_benchmark.csv")
        return

    plt.figure(figsize=(9, 6))
    colors = ['#757575', '#1976d2', '#2e7d32'] # Xám, Xanh Dương, Xanh Lá
    
    bars = plt.bar(times.keys(), times.values(), color=colors[:len(times)], width=0.6, edgecolor='black')
    
    plt.title("Execution Time Comparison", fontsize=14, fontweight='bold')
    plt.ylabel("Total Duration (Seconds)")
    plt.grid(axis='y', linestyle=':', alpha=0.6)
    
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, h, f"{h:.2f}s", ha='center', va='bottom', fontweight='bold', fontsize=11)
        
    plt.tight_layout()
    plt.savefig(os.path.join(TARGET_DIR, "2_time_comparison.png"), dpi=300)
    print("    -> Đã lưu: 2_time_comparison.png")
    plt.close()

if __name__ == "__main__":
    plot_training_trend()
    plot_time_comparison()
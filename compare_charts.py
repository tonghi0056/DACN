import matplotlib.pyplot as plt
import json
import os
import sys

def load_metrics(filepath):
    """Đọc dữ liệu từ file _metrics.json"""
    if not os.path.exists(filepath):
        print(f"[-] Không tìm thấy file: {filepath}")
        return None, None
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data['episodes'], data['rewards']

def plot_comparison(title, lines, filename_suffix):
    """
    Hàm vẽ biểu đồ chung.
    lines: List các tuple (Label, FilePath, Color, LineStyle)
    """
    plt.figure(figsize=(12, 6))
    
    has_data = False
    for label, path, color, style in lines:
        eps, rewards = load_metrics(path)
        if eps and rewards:
            plt.plot(eps, rewards, label=label, color=color, linestyle=style, linewidth=2)
            has_data = True
    
    if not has_data:
        print(f"[-] Bỏ qua biểu đồ '{title}' do thiếu dữ liệu.")
        plt.close()
        return

    plt.title(title, fontsize=14)
    plt.xlabel("Episode", fontsize=12)
    plt.ylabel("Average Reward", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Lưu biểu đồ
    os.makedirs("results/comparison_charts", exist_ok=True)
    save_path = f"results/comparison_charts/{filename_suffix}.png"
    plt.savefig(save_path)
    print(f"[+] Đã lưu biểu đồ: {save_path}")
    plt.close()

def main():
    # ĐỊNH NGHĨA ĐƯỜNG DẪN CÁC FILE METRICS
    # Lưu ý: Các file này được tạo ra từ main.py mới (đuôi _metrics.json)
    
    # 1. Baseline (Chưa học)
    BASE_RANDOM = "results/target_results/random_baseline_metrics.json"
    BASE_SARSA = "results/target_results/sarsa_baseline_metrics.json"
    BASE_QL = "results/target_results/q_learning_baseline_metrics.json"
    
    # 2. Evaluated (Đã học từ Mock mang sang test)
    EVAL_SARSA = "results/target_results/sarsa_evaluated_metrics.json"
    EVAL_QL = "results/target_results/q_learning_evaluated_metrics.json"
    
    # 3. Transfer (Học tiếp)
    TRANS_QL = "results/target_results/q_learning_transfer_final_metrics.json"

    # --- VẼ CÁC BIỂU ĐỒ THEO YÊU CẦU ---

    # Biểu đồ 1: Tổng hợp Random, SARSA, QL (Mốc ban đầu - Chưa học)
    plot_comparison(
        "Baseline Comparison (Untrained Agents)",
        [
            ("Random", BASE_RANDOM, "gray", "--"),
            ("SARSA (Untrained)", BASE_SARSA, "blue", "-"),
            ("Q-Learning (Untrained)", BASE_QL, "orange", "-")
        ],
        "1_baseline_comparison"
    )

    # Biểu đồ 2: SARSA - Chưa học vs Học rồi
    plot_comparison(
        "SARSA Improvement (Before vs After Training)",
        [
            ("SARSA (Untrained)", BASE_SARSA, "green", "--"), # Xanh: Chưa học
            ("SARSA (Trained)", EVAL_SARSA, "red", "-")       # Đỏ: Học rồi
        ],
        "2_sarsa_improvement"
    )

    # Biểu đồ 3: Q-Learning - Chưa học vs Học rồi
    plot_comparison(
        "Q-Learning Improvement (Before vs After Training)",
        [
            ("Q-Learning (Untrained)", BASE_QL, "green", "--"), # Xanh: Chưa học
            ("Q-Learning (Trained)", EVAL_QL, "red", "-")       # Đỏ: Học rồi
        ],
        "3_qlearning_improvement"
    )

    # Biểu đồ 4: Random vs SARSA (Học) vs QL (Học)
    plot_comparison(
        "Trained Agents vs Random Baseline",
        [
            ("Random Baseline", BASE_RANDOM, "gray", "--"),
            ("SARSA (Trained)", EVAL_SARSA, "blue", "-"),
            ("Q-Learning (Trained)", EVAL_QL, "orange", "-")
        ],
        "4_trained_vs_random"
    )

    # Biểu đồ 5: So sánh SARSA vs Q-Learning (Đã học)
    plot_comparison(
        "Algorithm Comparison: SARSA vs Q-Learning (Trained)",
        [
            ("SARSA (Trained)", EVAL_SARSA, "blue", "-"),
            ("Q-Learning (Trained)", EVAL_QL, "red", "-")
        ],
        "5_sarsa_vs_qlearning"
    )

    # Biểu đồ 6: Q-Learning (Học rồi) vs Q-Learning (Transfer)
    plot_comparison(
        "Transfer Learning Effect (Q-Learning)",
        [
            ("Q-Learning (Trained Only)", EVAL_QL, "blue", "--"),
            ("Q-Learning (Transfer/Fine-tuned)", TRANS_QL, "red", "-")
        ],
        "6_transfer_effect"
    )

if __name__ == "__main__":
    main()
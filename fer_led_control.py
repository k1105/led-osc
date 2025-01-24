import cv2
import time
import random
from math import ceil
from fer import FER
from pythonosc.udp_client import SimpleUDPClient

# デバイス情報
TARGET_IPS = ["192.168.8.101"]  # 使用するデバイスのIP
TARGET_PORT = 8000
OSC_ADDRESS = "/color"

# 表情と色のマッピング (RGB)
EMOTION_COLORS = {
    "happy": (245, 197, 15),    # 喜: 黄色
    "angry": (245, 26, 24),      # 怒: 赤
    "sad": (51, 65, 245),        # 哀: 青
    "neutral": (255, 255, 255),  # 楽: 白
    "fear": (104, 160, 133),     # 恐怖: 紫
    "surprise": (0, 255, 255)  # 驚き: シアン
}

# イージング関数 (easeInOutQuad)
def ease_in_out_quad(t):
    if t < 0.5:
        return 2 * t * t
    else:
        return -1 + (4 - 2 * t) * t

# 色を補間する関数
def interpolate_color(start_color, end_color, progress):
    r1, g1, b1 = start_color
    r2, g2, b2 = end_color
    r = int(r1 + (r2 - r1) * progress)
    g = int(g1 + (g2 - g1) * progress)
    b = int(b1 + (b2 - b1) * progress)
    return r, g, b

def send_colors_with_easing(colors, indices, target_color, duration, k, ips, port):
    """
    指定されたインデックスのユニット（k個の電球）をターゲット色に滑らかに遷移。
    """
    clients = [SimpleUDPClient(ip, port) for ip in ips]

    steps = int(duration * 60)  # 60FPS想定
    current_colors = colors[:]
    for step in range(steps + 1):
        progress = step / steps
        eased_progress = ease_in_out_quad(progress)

        # 選ばれたインデックスとその範囲の色を補間
        for idx in indices:
            for i in range(idx, idx + k):
                if i < len(current_colors):  # 範囲外をチェック
                    current_colors[i] = interpolate_color(current_colors[i], target_color, eased_progress)

        # OSCで送信
        formatted_colors = [
            0x00000000 | (r << 16) | (g << 8) | b for r, g, b in current_colors
        ]
        for client in clients:
            client.send_message(OSC_ADDRESS, formatted_colors)

        time.sleep(1 / 60)  # 60FPS

def main():
    # 初期状態ですべて白
    current_colors = [(255, 255, 255)] * 96
    clients = [SimpleUDPClient(ip, TARGET_PORT) for ip in TARGET_IPS]
    formatted_colors = [
        0x00000000 | (255 << 16) | (255 << 8) | 255 for _ in current_colors
    ]
    for client in clients:
        client.send_message(OSC_ADDRESS, formatted_colors)

    # FERのセットアップ
    detector = FER(mtcnn=True)

    # カメラのセットアップ
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("カメラを開けませんでした。")
        return

    print("表情検出を開始します。'q'キーで終了。")

    k = 3  # ユニットのサイズ
    while True:
        ret, frame = cap.read()
        if not ret:
            print("フレームを取得できませんでした。")
            break

        # 表情を検出
        result = detector.detect_emotions(frame)
        if result:
            emotions = result[0]["emotions"]
            dominant_emotion = max(emotions, key=emotions.get)
            intensity = emotions[dominant_emotion] * 100  # 0-100 の範囲にスケール
            n = ceil(intensity / 100 * 5)  # nを計算
            target_color = EMOTION_COLORS.get(dominant_emotion, (0, 0, 0))

            print(f"Detected emotion: {dominant_emotion}, intensity: {intensity:.2f}, n: {n}")

            # ランダムにn個のユニットを選択
            selected_indices = random.sample(range(96), n)

            # 色の遷移を開始
            send_colors_with_easing(
                current_colors, selected_indices, target_color, duration=2, k=k, ips=TARGET_IPS, port=TARGET_PORT
            )

            # 遷移後の状態を更新
            for idx in selected_indices:
                for i in range(idx, idx + k):
                    if i < len(current_colors):  # 範囲外をチェック
                        current_colors[i] = target_color

        # カメラ映像を表示
        cv2.imshow("Emotion Detection", frame)

        # 'q'キーで終了
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

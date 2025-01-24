import cv2
import time
from pythonosc.udp_client import SimpleUDPClient

# デバイス情報
TARGET_IPS = ["192.168.8.100", "192.168.8.101", "192.168.8.102"]  # 使用するデバイスのIP
TARGET_PORT = 8000
OSC_ADDRESS = "/color"

def extract_colors_from_frame(frame, num_samples=96):
    """
    フレームの中央を縦断し、上から順に指定された数だけ色をサンプリング。
    """
    height, width, _ = frame.shape
    center_x = width // 2  # 中央列
    step = height // num_samples  # 等間隔のステップ

    colors = []
    for i in range(num_samples):
        y = min(i * step, height - 1)  # サンプリング位置
        b, g, r = frame[y, center_x]
        col = (int(r * 1.0), int(g * 1.0), int(b * 1.2))
        col = gamma_correction(col)
        col = clamp_color(col)

        colors.append(col)  # RGB形式に変換
    return colors

def gamma_correction(color, gamma=2.2):
    return tuple(int((c / 255.0) ** gamma * 255) for c in color)

def clamp_color(col):
    return tuple(max(0, min(255, c)) for c in col)

def process_and_send(video_path, ips, port, interval=0.022):
    """
    映像をシーケンシャルに処理し、中央の96色をOSCで送信。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"動画ファイルを開けませんでした: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_duration = 1.0 / fps
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps

    print(f"Video FPS: {fps}, Total frames: {total_frames}, Duration: {video_duration:.2f} sec")

    clients = [SimpleUDPClient(ip, port) for ip in ips]

    start_time = time.time()  # プログラムの開始時刻
    frame_index = 0

    while True:
        elapsed_time = time.time() - start_time  # 実行開始からの経過時間
        target_frame_index = int(elapsed_time / frame_duration)  # 再生時刻に対応するフレーム

        # フレームのスキップを検知
        while frame_index < target_frame_index:
            ret, frame = cap.read()
            frame_index += 1

            # フレーム取得失敗時の処理
            if not ret or frame_index >= total_frames:
                print("動画が終了しました。")
                cap.release()
                return

        # 現在のフレームが正しく取得された場合のみ処理
        try:
            colors = extract_colors_from_frame(frame, num_samples=96)
            formatted_colors = [0x00000000 | (r << 16) | (g << 8) | b for r, g, b in colors]

            # OSCで送信
            for client in clients:
                try:
                    client.send_message(OSC_ADDRESS, formatted_colors)
                    print(f"Sent colors for frame {frame_index}")
                except ValueError as e:
                    print(f"Error sending to {client._address}: {e}")
        except UnboundLocalError:
            print("フレームの取得に失敗しました。")

        time.sleep(interval)  # 処理間隔


if __name__ == "__main__":
    video_path = "movie/color_tester.mp4"
    process_and_send(video_path, TARGET_IPS, TARGET_PORT)

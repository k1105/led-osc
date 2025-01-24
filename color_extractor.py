import sys
import cv2
import json
import numpy as np
from pythonosc.udp_client import SimpleUDPClient

# デバイス情報
TARGET_IPS = ["192.168.8.100", "192.168.8.101", "192.168.8.102"]
TARGET_PORT = 8000
OSC_ADDRESS = "/color"

def extract_colors_from_frame(frame, num_samples=150):
    """
    フレームの中央を縦断し、上から順に指定された数だけ色をサンプリング。
    """
    height, width, _ = frame.shape
    center_x = width // 2  # 中央列
    step = height // num_samples  # 等間隔のステップ

    colors = []
    for i in range(num_samples):
        y = min(i * step, height - 1)  # サンプル位置
        b, g, r = frame[y, center_x]  # OpenCVはBGR形式
        colors.append((int(r), int(g), int(b)))  # RGB形式に変換

    return colors

def process_video(video_path, output_file="palette.json", num_samples=150, frame_interval=30):
    """
    動画を読み込み、各フレームの中央から色を抽出してJSONに保存。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"動画ファイルを開けませんでした: {video_path}")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        print("総フレーム数を取得できませんでした。")
        sys.exit(1)

    print(f"動画から色を抽出します: {video_path}")
    frame_count = 0
    color_data = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            # フレーム中央から色を抽出
            sampled_colors = extract_colors_from_frame(frame, num_samples=num_samples)
            # 色データを保存
            color_data.append({
                "frame": frame_count,
                "colors": sampled_colors
            })

            print(f"Frame {frame_count}: {sampled_colors[:5]}... (truncated)")

        frame_count += 1

    cap.release()

    # JSONとして保存
    with open(output_file, "w") as f:
        json.dump(color_data, f, indent=4)

    print(f"抽出結果を {output_file} に保存しました。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python extract_colors.py <動画ファイルパス>")
        sys.exit(1)

    video_path = sys.argv[1]
    process_video(video_path)

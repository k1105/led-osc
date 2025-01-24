import cv2
import mediapipe as mp
from pythonosc.udp_client import SimpleUDPClient
import time

# デバイス情報
TARGET_IPS = ["192.168.8.101"]  # 使用するデバイスのIP
TARGET_PORT = 8000
OSC_ADDRESS = "/color"

# 表情と色のマッピング
EMOTION_COLORS = {
    "喜": (255, 255, 0),  # 黄色
    "怒": (255, 0, 0),    # 赤
    "哀": (0, 0, 255),    # 青
    "楽": (0, 255, 0)     # 緑
}

# Mediapipe描画ユーティリティ
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def classify_emotion(landmarks):
    """
    Mediapipeの顔ランドマークから表情を分類する。
    """
    # 簡易ロジック: 目の開き具合で表情を仮分類
    left_eye_ratio = landmarks[159][1] - landmarks[145][1]  # 左目の上下差
    right_eye_ratio = landmarks[386][1] - landmarks[374][1]  # 右目の上下差

    # ランダムな分類（簡易版、調整可能）
    if left_eye_ratio > 15 and right_eye_ratio > 15:
        return "楽"
    elif left_eye_ratio < 10 and right_eye_ratio < 10:
        return "哀"
    elif left_eye_ratio > right_eye_ratio:
        return "怒"
    else:
        return "喜"

def send_colors(emotion, ips, port):
    """
    表情に応じた色をLEDに送信。
    """
    clients = [SimpleUDPClient(ip, port) for ip in ips]
    r, g, b = EMOTION_COLORS[emotion]

    # 96個のLEDすべてに同じ色を設定
    colors = [0x00000000 | (r << 16) | (g << 8) | b] * 96

    for client in clients:
        client.send_message(OSC_ADDRESS, colors)
        print(f"Sent colors for emotion '{emotion}': {colors[0]:#08X}")

def main():
    # Mediapipeのセットアップ
    face_mesh = mp_face_mesh.FaceMesh(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # カメラのセットアップ
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("カメラを開けませんでした。")
        return

    print("表情検出を開始します。'q'キーで終了。")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("フレームを取得できませんでした。")
            break

        # Mediapipeで顔ランドマークを取得
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # ランドマークの座標を取得
                landmarks = [(int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])) for lm in face_landmarks.landmark]

                # 表情分類
                emotion = classify_emotion(landmarks)
                send_colors(emotion, TARGET_IPS, TARGET_PORT)  # 表情に応じた色を送信

                # ランドマークを描画
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
                )

                # 表情のラベルをフレームに表示
                cv2.putText(frame, f"Emotion: {emotion}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # カメラ映像を表示
        cv2.imshow("Emotion Detection", frame)

        # 'q'キーで終了
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

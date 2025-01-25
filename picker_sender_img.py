import cv2
from pythonosc.udp_client import SimpleUDPClient

# デバイス情報
TARGET_IPS = ["192.168.8.100", "192.168.8.101", "192.168.8.102"]  # 使用するデバイスのIP
TARGET_PORT = 8000
OSC_ADDRESS = "/color"

def extract_colors_from_image(image_path, num_samples=96, positions=("center", "left", "right")):
    """
    画像の指定された位置から色をサンプリング。
    """
    image = cv2.imread(image_path)  # 画像を読み込み
    if image is None:
        print(f"画像を開けませんでした: {image_path}")
        return None

    height, width, _ = image.shape
    step = height // num_samples  # 等間隔のステップ

    color_data = {}
    for pos in positions:
        if pos == "center":
            center_x = width // 2  # 中央列
        elif pos == "left":
            center_x = width // 4  # 左半分の中央列
        elif pos == "right":
            center_x = 3 * (width // 4)  # 右半分の中央列
        else:
            raise ValueError("Invalid position specified. Use 'center', 'left', or 'right'.")

        colors = []
        for i in range(num_samples):
            y = min(i * step, height - 1)  # サンプリング位置
            b, g, r = image[y, center_x]
            colors.append((int(r), int(g), int(b)))  # RGB形式に変換

        color_data[pos] = colors

    return color_data

def send_colors(color_data, ips, port):
    """
    抽出した色をOSCで送信。
    """
    clients = [SimpleUDPClient(ip, port) for ip in ips]

    for i, pos in enumerate(("center", "left", "right")):
        if pos not in color_data:
            print(f"No color data for position: {pos}")
            continue

        # RGB -> 0x00RRGGBB に変換
        formatted_colors = [0x00000000 | (r << 16) | (g << 8) | b for r, g, b in color_data[pos]]

        # OSCで送信
        try:
            clients[i].send_message(OSC_ADDRESS, formatted_colors)
            print(f"Sent colors for {pos} to device {TARGET_IPS[i]}")
        except ValueError as e:
            print(f"Error sending to {clients[i]._address}: {e}")

if __name__ == "__main__":
    image_path = "img/rwb.png"  # 画像ファイルのパス
    color_data = extract_colors_from_image(image_path, num_samples=96, positions=("center", "left", "right"))
    if color_data:
        send_colors(color_data, TARGET_IPS, TARGET_PORT)

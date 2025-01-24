import cv2
from pythonosc.udp_client import SimpleUDPClient

# デバイス情報
TARGET_IPS = ["192.168.8.101"]  # 使用するデバイスのIP
TARGET_PORT = 8000
OSC_ADDRESS = "/color"

def extract_colors_from_image(image_path, num_samples=96):
    """
    画像の中央を縦断し、上から順に指定された数だけ色をサンプリング。
    """
    image = cv2.imread(image_path)  # 画像を読み込み
    if image is None:
        print(f"画像を開けませんでした: {image_path}")
        return None

    height, width, _ = image.shape
    center_x = width // 2  # 中央列
    step = height // num_samples  # 等間隔のステップ

    colors = []
    for i in range(num_samples):
        y = min(i * step, height - 1)  # サンプリング位置
        b, g, r = image[y, center_x]
        print("r: "+str(r)+", g: "+str(g)+", b: "+str(b))
        colors.append((int(r), int(g), int(b)))  # RGB形式に変換

    return colors

def send_colors(colors, ips, port):
    """
    抽出した色をOSCで送信。
    """
    clients = [SimpleUDPClient(ip, port) for ip in ips]

    # RGB -> 0x00RRGGBB に変換
    formatted_colors = [0x00000000 | (r << 16) | (g << 8) | b for r, g, b in colors]

    # OSCで送信
    for client in clients:
        try:
            client.send_message(OSC_ADDRESS, formatted_colors)
            print(f"Sent colors: {formatted_colors[:96]}")
        except ValueError as e:
            print(f"Error sending to {client._address}: {e}")

if __name__ == "__main__":
    image_path = "img/color_tester.png"  # 画像ファイルのパス
    colors = extract_colors_from_image(image_path, num_samples=96)
    if colors:
        send_colors(colors, TARGET_IPS, TARGET_PORT)

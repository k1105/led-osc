import json
import time
from pythonosc.udp_client import SimpleUDPClient

# デバイス情報
TARGET_IPS = ["192.168.8.101"]
TARGET_PORT = 8000
OSC_ADDRESS = "/color"

def load_palette(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def send_colors_to_leds(palette_data, ips, port, interval=1/60):
    clients = [SimpleUDPClient(ip, port) for ip in ips]

    for entry in palette_data:
        colors = entry["colors"]
        # RGB -> 0x00RRGGBB に変換
        formatted_colors = [0x00000000 | (r << 16) | (g << 8) | b for r, g, b in colors]

        # OSCで送信
        for client in clients:
            client.send_message(OSC_ADDRESS, formatted_colors)
        print(f"Sent colors: {formatted_colors[:5]}... (truncated)")

        time.sleep(interval)

if __name__ == "__main__":
    palette_file = "palette.json"
    palette_data = load_palette(palette_file)
    send_colors_to_leds(palette_data, TARGET_IPS, TARGET_PORT)

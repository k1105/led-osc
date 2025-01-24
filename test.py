from pythonosc.udp_client import SimpleUDPClient
client = SimpleUDPClient("192.168.8.100", 8000)
client.send_message("/test", [0x00FFFFFF])
print("Test signal sent!")

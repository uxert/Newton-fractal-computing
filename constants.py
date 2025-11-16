import socket

# Get local IP address
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"Local IP: {local_ip}")

amqp_url: str = f"amqp://guest:guest@{local_ip}:5672/%2F"
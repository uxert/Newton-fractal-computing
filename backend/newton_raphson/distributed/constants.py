import socket

# Get local IP address
hostname = socket.gethostname()
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external address (doesn't actually send data)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

local_ip = get_local_ip()
print(f"Local IP: {local_ip}")

amqp_url: str = f"amqp://guest:guest@{local_ip}:5672/%2F"
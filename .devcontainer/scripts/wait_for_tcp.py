import socket
import sys
import time


host = sys.argv[1]
port = int(sys.argv[2])
timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 60
deadline = time.time() + timeout

while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            sys.exit(0)
    except OSError:
        time.sleep(1)

print(f"Timed out waiting for {host}:{port}", file=sys.stderr)
sys.exit(1)

"""Wait for real HTTP responses without printing service bodies."""
import time
import urllib.error
import urllib.request

for port in (7005, 7006, 7004):
    deadline = time.monotonic() + 180
    while True:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3):
                break
        except urllib.error.HTTPError as error:
            # A route-level 404/401 proves the HTTP listener is serving requests.
            if error.code < 500:
                break
        except (OSError, urllib.error.URLError):
            pass
        if time.monotonic() >= deadline:
            raise SystemExit(f"Service readiness timed out on port {port}")
        time.sleep(2)
print("PASS: all three API2 HTTP listeners are ready")

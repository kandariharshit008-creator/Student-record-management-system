import json
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


BASE_DIR = Path(__file__).resolve().parent
APP_URL = "http://127.0.0.1:8000"


def server_is_ready() -> bool:
    try:
        with urlopen(f"{APP_URL}/api/stats", timeout=1) as response:
            stats = json.loads(response.read())
        return all(key in stats for key in ("total", "active", "courses"))
    except (OSError, URLError, json.JSONDecodeError):
        return False


def main() -> None:
    if not server_is_ready():
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=BASE_DIR,
            creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        )

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if server_is_ready():
                break
            time.sleep(0.5)
        else:
            raise RuntimeError(
                "The app did not start. Check the server window and install "
                "requirements with: python -m pip install -r requirements.txt"
            )

    webbrowser.open(APP_URL)
    print(f"Student Record Management is open at {APP_URL}.")


if __name__ == "__main__":
    main()

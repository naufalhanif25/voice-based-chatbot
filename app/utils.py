import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "..", "logs")

os.makedirs(LOGS_DIR, exist_ok = True)

def generate_log(message: str) -> None:
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    log_message = f"[{time}] {message}"
    
    with open(os.path.join(LOGS_DIR, f"{date}.log"), "a") as log_file:
        log_file.write(log_message + "\n")

def read_instruction(path: str) -> str:
    with open(path, "r", encoding = "utf-8") as f:
        return f.read().strip()
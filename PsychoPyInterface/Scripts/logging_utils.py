# Scripts/logging_utils.py
import os
from datetime import datetime

def create_log_file(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    return open(filepath, "w")

def log_message(log_file, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write(f"{timestamp} - {message}\n")
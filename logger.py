import os
import datetime
import config


def log_activity(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"

    log_path = config.LOG_FILE

    folder = os.path.dirname(log_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    with open(log_path, "a") as f:
        f.write(log_line)

    print("Log:", message)

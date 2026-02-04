import datetime

def log_activity(message):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    with open("activity_log.txt", "a") as file:
        file.write(f"[{timestamp}] {message}\n")

    print(f"Logged: {message}")

if __name__ == "__main__":
    log_activity("System started")
    log_activity("Dashboard viewed")
    log_activity("Video scan initiated")

import time
import config

def scan_new_uploads():
    print(f"Scanning folder: {config.SCAN_FOLDER}")
    print("Looking for new videos...")

    # Prototype behavior (future me automation add karenge)
    sample_files = ["clip_01.mp4", "clip_02.mp4"]

    for file in sample_files:
        print(f"Checking: {file}")
        time.sleep(1)

    print("Scan completed.")

if __name__ == "__main__":
    scan_new_uploads()

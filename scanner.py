import time

def scan_new_uploads(folder="uploads"):
    print(f"Scanning folder: {folder}")
    print("Looking for new videos...")

    # Prototype behaviour (real system me yaha automation aayega)
    sample_files = ["clip_01.mp4", "clip_02.mp4"]

    for file in sample_files:
        print(f"Checking: {file}")
        time.sleep(1)

    print("Scan completed.")

if __name__ == "__main__":
    scan_new_uploads()

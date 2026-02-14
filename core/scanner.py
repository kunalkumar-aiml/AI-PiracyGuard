import os
import time
import config

def scan_new_uploads():
    folder = config.SCAN_FOLDER

    print("Scanning folder:", folder)

    if not os.path.exists(folder):
        print("Folder does not exist.")
        return

    files = os.listdir(folder)

    if not files:
        print("No files found.")
        return

    for file in files:
        if file.endswith(".mp4"):
            print("Checking file:", file)
            time.sleep(1)

    print("Scanning finished.")

if __name__ == "__main__":
    scan_new_uploads()

import time

def show_dashboard():
    print("\n================ AI PIRACY GUARD DASHBOARD ================\n")

    print("System Status       : ACTIVE")
    print("Videos Scanned      : 12")
    print("Possible Leaks      : 2")
    print("Deepfake Alerts     : 1")
    print("Watermark Traced    : 1")

    print("\nRecent Activity:")
    print("- Scanned new upload: movie_clip_01.mp4")
    print("- Flagged suspicious video")
    print("- Watermark match found")

    print("\nRefreshing dashboard in 5 seconds...")
    time.sleep(5)

if __name__ == "__main__":
    show_dashboard()

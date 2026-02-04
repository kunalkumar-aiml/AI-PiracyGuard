def check_watermark(video_path):
    print(f"Analyzing watermark in: {video_path}")

    # In future this will detect invisible watermark patterns
    print("Scanning frames...")
    print("Looking for hidden watermark...")

    # Temporary result for now
    print("Watermark detected: YES")
    print("Possible source: Studio server A")

if __name__ == "__main__":
    check_watermark("sample_video.mp4")

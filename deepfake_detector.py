import random

def simple_deepfake_check(video_name):
    print(f"Checking video: {video_name}")

    # This is a simple prototype, not a full model yet
    score = random.uniform(0, 1)

    print(f"Deepfake risk score: {round(score, 2)}")

    if score > 0.6:
        print("Warning: This video might be manipulated.")
    else:
        print("Video looks normal.")

if __name__ == "__main__":
    simple_deepfake_check("sample_video.mp4")

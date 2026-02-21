import random

def analyze_video(video_path):
    """
    Simulated deepfake analysis.
    Returns score between 0 and 100
    """

    # Later: replace with real ML model
    score = random.randint(0, 100)

    return {
        "deepfake_score": score,
        "is_suspected": score > 60
    }

import random

def calculate_risk(video_name):
    print(f"Analyzing risk for: {video_name}")

    # Prototype risk score (future me real ML model aayega)
    risk = round(random.uniform(0, 1), 2)

    if risk > 0.7:
        level = "HIGH"
    elif risk > 0.4:
        level = "MEDIUM"
    else:
        level = "LOW"

    print(f"Risk score: {risk} | Level: {level}")
    return risk

if __name__ == "__main__":
    calculate_risk("clip_02.mp4")

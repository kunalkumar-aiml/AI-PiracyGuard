import config

def calculate_risk(video_name):
    score = 0

    name = video_name.lower()

    # Simple rule based scoring
    if "cam" in name:
        score += 0.4

    if "hd" in name:
        score += 0.2

    if "official" in name:
        score -= 0.3

    if name.endswith(".mp4"):
        score += 0.2

    # Make sure score stays between 0 and 1
    if score < 0:
        score = 0

    if score > 1:
        score = 1

    print("Risk score:", score)

    if score >= config.PIRACY_THRESHOLD:
        print("High piracy risk")
    else:
        print("Low or medium risk")

    return score


if __name__ == "__main__":
    calculate_risk("movie_cam_hd.mp4")

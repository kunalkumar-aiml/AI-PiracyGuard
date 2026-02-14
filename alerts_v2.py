from models import risk_model
import config

def smart_alert(video_name):
    print("Running alert for:", video_name)

    risk = risk_model.calculate_risk(video_name)

    if risk >= config.PIRACY_THRESHOLD:
        print("Alert: Possible pirated content detected")
    else:
        print("No serious issue detected")

if __name__ == "__main__":
    smart_alert("movie_cam_hd.mp4")

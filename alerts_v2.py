import risk_model

def smart_alert(video_name):
    print(f"\nRunning smart alert for: {video_name}")

    risk = risk_model.calculate_risk(video_name)

    if risk > 0.7:
        print("🚨 HIGH RISK — Immediate action required!")
    elif risk > 0.4:
        print("⚠️ Medium risk — monitor closely.")
    else:
        print("✅ Low risk — safe for now.")

if __name__ == "__main__":
    smart_alert("clip_02.mp4")

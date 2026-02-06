def send_alert(video_name, risk_level):
    print(f"ALERT for: {video_name}")

    if risk_level > 0.7:
        print("🚨 HIGH RISK — immediate review needed!")
    elif risk_level > 0.4:
        print("⚠️ Medium risk — keep monitoring.")
    else:
        print("✅ Low risk — normal activity.")

if __name__ == "__main__":
    send_alert("clip_02.mp4", 0.82)

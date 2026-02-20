from core.detection_engine import DETECTION_RESULTS


def generate_summary():
    if not DETECTION_RESULTS:
        return {
            "total_videos": 0,
            "piracy_matches": 0,
            "safe_videos": 0,
            "average_risk_score": 0,
            "risk_distribution": {
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            },
            "high_risk_videos": []
        }

    total = len(DETECTION_RESULTS)
    high = 0
    medium = 0
    low = 0
    total_risk = 0
    high_risk_list = []

    for result in DETECTION_RESULTS:
        level = result["risk_level"]
        total_risk += result["risk_score"]

        if level == "HIGH":
            high += 1
            high_risk_list.append(result["video_path"])
        elif level == "MEDIUM":
            medium += 1
        else:
            low += 1

    average_risk = round(total_risk / total, 2)

    return {
        "total_videos": total,
        "piracy_matches": high,
        "safe_videos": low,
        "average_risk_score": average_risk,
        "risk_distribution": {
            "HIGH": high,
            "MEDIUM": medium,
            "LOW": low
        },
        "high_risk_videos": high_risk_list
    }

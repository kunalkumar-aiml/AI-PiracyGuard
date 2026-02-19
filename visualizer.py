from core.detection_engine import DETECTION_RESULTS


def generate_summary():
    if not DETECTION_RESULTS:
        return {
            "total_videos": 0,
            "piracy_matches": 0,
            "safe_videos": 0
        }

    total = len(DETECTION_RESULTS)
    piracy_count = 0
    safe_count = 0

    for result in DETECTION_RESULTS:
        if result["status"] == "Pirated":
            piracy_count += 1
        else:
            safe_count += 1

    return {
        "total_videos": total,
        "piracy_matches": piracy_count,
        "safe_videos": safe_count
    }

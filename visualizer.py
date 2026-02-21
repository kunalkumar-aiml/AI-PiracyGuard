from core.detection_engine import DETECTION_RESULTS


def show_visual_summary():
    print("\n========== AI PIRACY GUARD SUMMARY ==========\n")

    if not DETECTION_RESULTS:
        print("No scan data available.\n")
        return

    total = len(DETECTION_RESULTS)
    high = 0
    medium = 0
    low = 0

    for result in DETECTION_RESULTS:
        level = result["risk_level"]

        if level == "HIGH":
            high += 1
        elif level == "MEDIUM":
            medium += 1
        else:
            low += 1

    print(f"Total Videos Scanned : {total}")
    print(f"HIGH Risk            : {high}")
    print(f"MEDIUM Risk          : {medium}")
    print(f"LOW Risk             : {low}")

    print("\nSystem Status: ACTIVE AND MONITORING")
    print("============================================\n")

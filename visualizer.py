from core.detection_engine import DETECTION_RESULTS


def show_visual_summary():
    print("\n========== AI PIRACY GUARD SUMMARY ==========\n")

    if not DETECTION_RESULTS:
        print("No scan data available.\n")
        return

    total = len(DETECTION_RESULTS)
    piracy_count = 0
    safe_count = 0

    for result in DETECTION_RESULTS:
        if result["status"] == "Pirated":
            piracy_count += 1
        else:
            safe_count += 1

    print(f"Total Videos Scanned : {total}")
    print(f"Piracy Matches       : {piracy_count}")
    print(f"Safe Videos          : {safe_count}")

    print("\nSystem Status: ACTIVE AND MONITORING")
    print("============================================\n")

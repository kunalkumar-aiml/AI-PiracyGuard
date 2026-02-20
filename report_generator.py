import os
import json
import datetime
from core.detection_engine import DETECTION_RESULTS


def generate_report():
    if not DETECTION_RESULTS:
        return

    if not os.path.exists("reports"):
        os.makedirs("reports")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/scan_{timestamp}.json"

    report_data = {
        "generated_at": timestamp,
        "total_videos": len(DETECTION_RESULTS),
        "results": DETECTION_RESULTS
    }

    with open(filename, "w") as f:
        json.dump(report_data, f, indent=4)

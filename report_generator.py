import json
import os
from datetime import datetime
from core.detection_engine import DETECTION_RESULTS


REPORT_DIR = "reports"


def generate_report():
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)

    if not DETECTION_RESULTS:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{REPORT_DIR}/forensic_report_{timestamp}.json"

    report_data = {
        "generated_at": datetime.now().isoformat(),
        "total_videos": len(DETECTION_RESULTS),
        "results": DETECTION_RESULTS
    }

    with open(filename, "w") as f:
        json.dump(report_data, f, indent=4)

    print(f"Forensic report saved: {filename}")

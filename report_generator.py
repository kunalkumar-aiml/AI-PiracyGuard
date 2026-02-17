import os
import json
import config
from core.detection_engine import DETECTION_RESULTS


def generate_report():
    print("\n===== SCAN REPORT =====\n")

    if not DETECTION_RESULTS:
        print("No results available.")
        return

    report_lines = []
    report_lines.append("AI Piracy Guard Report\n")
    report_lines.append("----------------------------\n")

    for result in DETECTION_RESULTS:
        line1 = f"Video: {result['video']}\n"
        line2 = f"Similarity: {result['similarity']}%\n"
        line3 = f"Status: {result['status']}\n"
        line4 = "----------------------------\n"

        print(line1.strip())
        print(line2.strip())
        print(line3.strip())
        print("----------------------------")

        report_lines.extend([line1, line2, line3, line4])

    # Save TXT report
    txt_path = config.REPORT_FILE

    folder = os.path.dirname(txt_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    with open(txt_path, "w") as f:
        f.writelines(report_lines)

    # Save JSON report
    json_path = txt_path.replace(".txt", ".json")

    with open(json_path, "w") as jf:
        json.dump(DETECTION_RESULTS, jf, indent=4)

    print("\nReport saved to:")
    print(txt_path)
    print(json_path)
    print("\nReport generation completed.\n")

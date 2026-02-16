import os
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

    # Save to file
    report_path = config.REPORT_FILE

    # make sure folder exists
    folder = os.path.dirname(report_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    with open(report_path, "w") as f:
        f.writelines(report_lines)

    print("\nReport saved to:", report_path)
    print("\nReport generation completed.\n")

from core import scanner
from core import alerts_v2
from report_generator import generate_report
from logger import log_activity
from visualizer import show_visual_summary
import os
import config

def run_pipeline():
    print("\n===== AI PIRACY GUARD PIPELINE START =====\n")

    log_activity("Pipeline started")

    folder = config.SCAN_FOLDER

    if not os.path.exists(folder):
        print("Upload folder not found.")
        return

    files = os.listdir(folder)

    if not files:
        print("No files to process.")
        return

    for file in files:
        if file.endswith(".mp4"):
            print("\nProcessing:", file)
            alerts_v2.smart_alert(file)

    generate_report()
    show_visual_summary()

    log_activity("Pipeline finished")
    print("\n===== PIPELINE FINISHED =====\n")


if __name__ == "__main__":
    run_pipeline()

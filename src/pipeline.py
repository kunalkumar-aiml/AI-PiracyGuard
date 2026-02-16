import os
import config
from core import scanner
from core import detection_engine
from logger import log_activity
from report_generator import generate_report
from visualizer import show_visual_summary


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

    # Register first file as known reference (demo purpose)
    first_video = None

    for file in files:
        if file.endswith(".mp4"):
            first_video = os.path.join(folder, file)
            break

    if first_video:
        detection_engine.register_known_video(first_video)

    for file in files:
        if file.endswith(".mp4"):
            full_path = os.path.join(folder, file)
            detection_engine.check_video(full_path)

    generate_report()
    show_visual_summary()

    log_activity("Pipeline finished")

    print("\n===== PIPELINE FINISHED =====\n")


if __name__ == "__main__":
    run_pipeline()

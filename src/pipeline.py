import os
import time
import config
from core import detection_engine
from logger import log_activity
from report_generator import generate_report
from visualizer import show_visual_summary


def run_pipeline():
    print("\n===== AI PIRACY GUARD PIPELINE START =====\n")

    start_time = time.time()
    log_activity("Pipeline started")

    folder = config.SCAN_FOLDER

    if not os.path.exists(folder):
        print("Upload folder not found.")
        log_activity("Upload folder not found")
        return

    files = os.listdir(folder)

    if not files:
        print("No files to process.")
        log_activity("No files found in upload folder")
        return

    first_video = None
    total_processed = 0

    for file in files:
        if file.endswith(".mp4"):
            first_video = os.path.join(folder, file)
            break

    if first_video:
        detection_engine.register_known_video(first_video)
        log_activity(f"Registered reference video: {first_video}")

    for file in files:
        if file.endswith(".mp4"):
            full_path = os.path.join(folder, file)

            log_activity(f"Processing file: {file}")
            detection_engine.check_video(full_path)

            total_processed += 1

    generate_report()
    show_visual_summary()

    end_time = time.time()
    duration = round(end_time - start_time, 2)

    log_activity(f"Total files processed: {total_processed}")
    log_activity(f"Total scan time: {duration} seconds")
    log_activity("Pipeline finished")

    print(f"\nTotal files processed: {total_processed}")
    print(f"Total scan time: {duration} seconds")
    print("\n===== PIPELINE FINISHED =====\n")


if __name__ == "__main__":
    run_pipeline()

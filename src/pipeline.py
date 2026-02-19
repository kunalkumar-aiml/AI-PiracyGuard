import os
import time
import config

from core import detection_engine
from logger import log_activity
from report_generator import generate_report
from visualizer import generate_summary


def run_pipeline():
    print("\n===== AI PIRACY GUARD PIPELINE START =====\n")

    start_time = time.time()
    log_activity("Pipeline started")

    folder = config.SCAN_FOLDER

    if not os.path.exists(folder):
        log_activity("Upload folder not found")
        return

    files = os.listdir(folder)

    if not files:
        log_activity("No files found in upload folder")
        return

    total_processed = 0
    first_video = None

    # Register first video as reference
    for file in files:
        if file.endswith(".mp4"):
            first_video = os.path.join(folder, file)
            break

    if first_video:
        detection_engine.register_known_video(first_video)
        log_activity(f"Registered reference video: {first_video}")

    # Scan all videos
    for file in files:
        if file.endswith(".mp4"):
            full_path = os.path.join(folder, file)

            log_activity(f"Processing file: {file}")
            detection_engine.check_video(full_path)

            total_processed += 1

    generate_report()

    summary = generate_summary()

    end_time = time.time()
    duration = round(end_time - start_time, 2)

    log_activity(f"Total files processed: {total_processed}")
    log_activity(f"Total scan time: {duration} seconds")
    log_activity("Pipeline finished")

    print("\n===== PIPELINE FINISHED =====\n")

    return summary

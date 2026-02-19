import sys

from src.pipeline import run_pipeline
from core.detection_engine import register_known_video
from visualizer import show_visual_summary
from db.db_manager import get_db_stats


def main():
    print("Starting AI Piracy Guard...\n")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 main.py --run")
        print("  python3 main.py --register <video_path>")
        print("  python3 main.py --stats")
        print("  python3 main.py --db-info")
        return

    command = sys.argv[1]

    # RUN FULL PIPELINE
    if command == "--run":
        run_pipeline()

    # REGISTER KNOWN VIDEO
    elif command == "--register":
        if len(sys.argv) < 3:
            print("Please provide video path.")
            return

        video_path = sys.argv[2]
        register_known_video(video_path)

    # SHOW LIVE STATS
    elif command == "--stats":
        show_visual_summary()

    # DATABASE INFO
    elif command == "--db-info":
        stats = get_db_stats()
        print("\nDatabase Information:")
        print(f"Total Registered Videos: {stats['total_registered_videos']}\n")

    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()

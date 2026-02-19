import sys
from src.pipeline import run_pipeline
from core.detection_engine import register_known_video
from visualizer import show_visual_summary


def main():
    print("Starting AI Piracy Guard...\n")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 main.py --run")
        print("  python3 main.py --register <video_path>")
        print("  python3 main.py --stats")
        return

    command = sys.argv[1]

    if command == "--run":
        run_pipeline()

    elif command == "--register":
        if len(sys.argv) < 3:
            print("Please provide video path.")
            return
        video_path = sys.argv[2]
        register_known_video(video_path)

    elif command == "--stats":
        show_visual_summary()

    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()

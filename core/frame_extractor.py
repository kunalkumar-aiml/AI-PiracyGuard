import cv2
import os


def extract_frames(video_path, step=30):
    if not os.path.exists(video_path):
        print("Video file not found:", video_path)
        return []

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Unable to open video:", video_path)
        return []

    frames = []
    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_count % step == 0:
            frames.append(frame)

        frame_count += 1

    cap.release()

    print("Frames extracted:", len(frames))
    return frames

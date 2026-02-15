import cv2
import numpy as np
from core.frame_extractor import extract_frames

def compute_frame_hash(frame):
  
    resized = cv2.resize(frame, (8, 8))
    
  
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    

    avg = gray.mean()
    
   
    hash_bits = gray > avg
    
  
    hash_string = ''.join(['1' if bit else '0' for row in hash_bits for bit in row])
    
    return hash_string


def generate_video_fingerprint(video_path):
    frames = extract_frames(video_path)
    
    if not frames:
        print("No frames extracted.")
        return None
    
    hashes = []
    
    for frame in frames:
        frame_hash = compute_frame_hash(frame)
        hashes.append(frame_hash)
    
    print("Generated fingerprint for video.")
    return hashes


if __name__ == "__main__":
    generate_video_fingerprint("sample.mp4")

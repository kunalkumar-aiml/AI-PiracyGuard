def format_video_name(name):
    return name.lower().replace(" ", "_")

def print_header(title):
    print("\n==============================")
    print(title)
    print("==============================\n")

if __name__ == "__main__":
    print_header("AI Piracy Guard Utils")
    print(format_video_name("Sample Video Clip"))

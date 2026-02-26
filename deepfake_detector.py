from models.deepfake_model import DeepfakeModel

model = DeepfakeModel()
model.load()


def analyze_video(video_path):
    """
    Returns structured deepfake analysis
    """

    probability = model.predict(video_path)
    score = round(probability * 100, 2)

    return {
        "deepfake_score": score,
        "is_suspected": score > 60
    }

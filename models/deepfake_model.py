import random

class DeepfakeModel:
    def __init__(self):
        self.model_name = "DeepfakeNet_v1"
        self.loaded = False

    def load(self):
        # Placeholder for real model loading
        self.loaded = True

    def predict(self, video_path):
        if not self.loaded:
            raise Exception("Model not loaded")

        # Simulated probability (later replace with real ML inference)
        probability = random.uniform(0, 1)

        return probability

class MetricsEngine:
    def __init__(self):
        self.tp = 0
        self.fp = 0
        self.tn = 0
        self.fn = 0

    def update(self, predicted_positive, actual_positive):
        if predicted_positive and actual_positive:
            self.tp += 1
        elif predicted_positive and not actual_positive:
            self.fp += 1
        elif not predicted_positive and not actual_positive:
            self.tn += 1
        elif not predicted_positive and actual_positive:
            self.fn += 1

    def calculate(self):
        precision = self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0
        recall = self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0
        accuracy = (self.tp + self.tn) / (
            self.tp + self.fp + self.tn + self.fn
        ) if (self.tp + self.fp + self.tn + self.fn) > 0 else 0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "accuracy": round(accuracy, 4),
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn
        }

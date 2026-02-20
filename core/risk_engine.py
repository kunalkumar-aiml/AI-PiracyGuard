def calculate_risk(similarity_score, deepfake_score=0, watermark_flag=False):
    """
    Returns structured risk analysis
    """

    risk_score = 0

    # Piracy similarity weight
    risk_score += similarity_score * 0.6

    # Deepfake detection weight
    risk_score += deepfake_score * 0.3

    # Watermark tampering weight
    if watermark_flag:
        risk_score += 10

    risk_score = min(100, round(risk_score, 2))

    if risk_score >= 75:
        level = "HIGH"
    elif risk_score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "explanation": {
            "similarity_weight": similarity_score,
            "deepfake_weight": deepfake_score,
            "watermark_flag": watermark_flag
        }
    }

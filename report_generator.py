import json
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Table
from core.detection_engine import DETECTION_RESULTS

REPORT_DIR = "reports"


def generate_report():
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)

    if not DETECTION_RESULTS:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON REPORT
    json_file = f"{REPORT_DIR}/forensic_report_{timestamp}.json"

    json_data = {
        "generated_at": datetime.now().isoformat(),
        "total_videos": len(DETECTION_RESULTS),
        "results": DETECTION_RESULTS
    }

    with open(json_file, "w") as f:
        json.dump(json_data, f, indent=4)

    # PDF REPORT
    pdf_file = f"{REPORT_DIR}/forensic_report_{timestamp}.pdf"
    doc = SimpleDocTemplate(pdf_file)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("AI PIRACY GUARD - FORENSIC REPORT", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Generated At: {datetime.now().isoformat()}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    data = [["Video", "Similarity", "Deepfake", "Risk Score", "Risk Level"]]

    for result in DETECTION_RESULTS:
        data.append([
            result["video_path"],
            str(result["similarity"]),
            str(result["deepfake_score"]),
            str(result["risk_score"]),
            result["risk_level"]
        ])

    table = Table(data)
    elements.append(table)

    doc.build(elements)

    print(f"Reports saved: {json_file} and {pdf_file}")

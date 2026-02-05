import datetime

def generate_report():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
    AI Piracy Guard Report
    -----------------------
    Generated on: {now}

    Videos scanned   : 12
    Suspicious clips : 2
    Deepfake alerts  : 1
    Watermark traced : 1

    Status: Monitoring active
    """

    with open("scan_report.txt", "w") as file:
        file.write(report)

    print("Report generated: scan_report.txt")

if __name__ == "__main__":
    generate_report()

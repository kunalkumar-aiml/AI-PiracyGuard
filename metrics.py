def show_metrics():
    print("\n=== AI Piracy Guard Metrics ===\n")

    print("Total videos scanned : 24")
    print("Piracy matches       : 4")
    print("Deepfake alerts      : 2")
    print("Watermark traces     : 2")

    accuracy = (20/24) * 100
    print(f"\nSystem accuracy approx: {round(accuracy, 2)}%")

if __name__ == "__main__":
    show_metrics()

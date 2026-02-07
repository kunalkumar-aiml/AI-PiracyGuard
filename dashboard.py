import time
import metrics
import utils

def show_dashboard():
    utils.print_header("AI PIRACY GUARD DASHBOARD")

    print("System Status       : ACTIVE")
    print("Monitoring Mode     : Continuous\n")

    metrics.show_metrics()

    print("\nRefreshing dashboard in 5 seconds...")
    time.sleep(5)

if __name__ == "__main__":
    show_dashboard()

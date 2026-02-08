import scanner
import dashboard
import report_generator
import logger

def run_pipeline():
    print("\n===== AI PIRACY GUARD PIPELINE START =====\n")

    logger.log_activity("Pipeline started")

    print("Step 1: Scanning uploads...")
    scanner.scan_new_uploads()
    logger.log_activity("Scanning completed")

    print("\nStep 2: Updating dashboard...")
    dashboard.show_dashboard()
    logger.log_activity("Dashboard updated")

    print("\nStep 3: Generating report...")
    report_generator.generate_report()
    logger.log_activity("Report generated")

    print("\n===== PIPELINE FINISHED =====")
    logger.log_activity("Pipeline finished")

if __name__ == "__main__":
    run_pipeline()

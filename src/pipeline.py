from core import scanner
import dashboard
import report_generator
import logger
import alerts_v2
import visualizer

def run_pipeline():
    print("\n===== AI PIRACY GUARD PIPELINE START =====\n")

    logger.log_activity("Pipeline started")

    print("Step 1: Scanning uploads...")
    scanner.scan_new_uploads()
    logger.log_activity("Scanning completed")

    print("\nStep 2: Running risk analysis...")
    alerts_v2.smart_alert("clip_02.mp4")
    logger.log_activity("Risk analysis completed")

    print("\nStep 3: Updating dashboard...")
    dashboard.show_dashboard()
    logger.log_activity("Dashboard updated")

    print("\nStep 4: Generating report...")
    report_generator.generate_report()
    logger.log_activity("Report generated")

    print("\nStep 5: Showing visual summary...")
    visualizer.show_visual_summary()
    logger.log_activity("Visualization displayed")

    print("\n===== PIPELINE FINISHED =====")
    logger.log_activity("Pipeline finished")

if __name__ == "__main__":
    run_pipeline()

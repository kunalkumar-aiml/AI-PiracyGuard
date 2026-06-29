"""Command Line Interface (CLI) entrypoint for AI-PiracyGuard.

Allows running forensic pipelines, registering files, and fetching status
directly from the terminal.
"""

import os
import sys

# Load local piracyguard package
from piracyguard.config import settings
from piracyguard.database.session import session_scope, init_database
from piracyguard.services.scan_service import ScanService
from piracyguard.services.job_service import JobService
from piracyguard.logging_config import setup_logging


def print_banner() -> None:
    """Print standard ASCI banner."""
    print("=" * 60)
    print("             AI PIRACY GUARD — MEDIA FORENSICS CLI             ")
    print("=" * 60)


def main() -> None:
    # Set up basic console logging for CLI
    setup_logging(level="WARNING", json_format=False)

    # Auto-initialize database schema if missing
    init_database()

    scan_service = ScanService()
    job_service = JobService(scan_service)

    if len(sys.argv) < 2:
        print_banner()
        print("Usage:")
        print("  python3 main.py --run                     - Scan uploads folder")
        print("  python3 main.py --register <path>         - Register known reference video")
        print("  python3 main.py --stats                   - View aggregated database stats")
        print("  python3 main.py --db-info                 - Fetch database counts")
        print("=" * 60)
        return

    command = sys.argv[1]

    # ── RUN FULL SCAN PIPELINE ──
    if command == "--run":
        print_banner()
        print("[*] Enqueuing background scan job for uploads directory...")
        
        # Ensure uploads folder exists
        settings.ensure_directories()
        upload_folder = str(settings.BASE_DIR / settings.UPLOAD_DIR)

        with session_scope() as db:
            job_uuid = job_service.start_scan_job(db, upload_folder)
            print(f"[+] Scan enqueued. Job ID: {job_uuid}")
            print("[*] Processing started in background executor...")
            
            # Poll status in CLI for direct feedback
            print("[*] Processing files...")
            while True:
                time_to_wait = 1
                status = job_service.get_job_status(db, job_uuid)
                curr_status = status.get("status")
                
                if curr_status in ("completed", "failed", "cancelled"):
                    print(f"\n[+] Job status: {curr_status.upper()}")
                    if curr_status == "completed":
                        print(f"[+] Successfully scanned: {status.get('processed_files')}/{status.get('total_files')} files.")
                        # Print summary table
                        results = status.get("results", [])
                        if results:
                            print("\nScan Results Summary:")
                            print("-" * 75)
                            print(f"{'Filename':25s} | {'Similarity':12s} | {'Deepfake':10s} | {'Risk Level':10s}")
                            print("-" * 75)
                            for r in results:
                                fname = os.path.basename(r['video_path'])
                                if len(fname) > 25:
                                    fname = fname[:22] + "..."
                                print(f"{fname:25s} | {r['similarity']:10.1f}% | {r['deepfake_score']:8.1f}% | {r['risk_level']:10s}")
                            print("-" * 75)
                    else:
                        print(f"[-] Scan job failed. Error: {status.get('error_message')}")
                    break
                
                # Simple progress dots
                sys.stdout.write(".")
                sys.stdout.flush()
                import time
                time.sleep(time_to_wait)

    # ── REGISTER KNOWN REFERENCE VIDEO ──
    elif command == "--register":
        if len(sys.argv) < 3:
            print("Error: Please provide target video path.")
            return

        video_path = sys.argv[2]
        print(f"[*] Extracting fingerprint for: {video_path}")

        try:
            with session_scope() as db:
                db_fp = scan_service.register_reference_video(db, video_path)
            print(f"[+] Success! Registered original reference.")
            print(f"    UUID: {db_fp.uuid}")
            print(f"    Frames: {db_fp.frame_count} | Duration: {db_fp.duration_seconds}s")
        except Exception as e:
            print(f"[-] Registration failed: {e}")

    # ── SHOW SCAN METRICS ──
    elif command == "--stats":
        print_banner()
        with session_scope() as db:
            stats = scan_service.get_stats(db)
        
        print("\nForensic Dashboard Stats:")
        print(f"  Total Registered Reference Videos : {stats['total_registered_videos']}")
        print(f"  Total Video Scans Conducted       : {stats['total_scans']}")
        print("\n  Threat Level Distribution:")
        for lvl, count in stats["threat_distribution"].items():
            print(f"    - {lvl:9s} : {count}")
        print("=" * 60)

    # ── DATABASE SCHEMA STATS ──
    elif command == "--db-info":
        print_banner()
        with session_scope() as db:
            stats = scan_service.get_stats(db)
        print(f"[+] Total Registered Fingerprints: {stats['total_registered_videos']}")
        print(f"[+] Total Historical Scan Records: {stats['total_scans']}")
        print("=" * 60)

    else:
        print(f"Unknown option: {command}. Run without arguments for help.")


if __name__ == "__main__":
    main()

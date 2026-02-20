import threading
import uuid
from src.pipeline import run_pipeline

JOBS = {}


def start_background_scan():
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "running"}

    thread = threading.Thread(target=_run_job, args=(job_id,))
    thread.start()

    return job_id


def _run_job(job_id):
    try:
        run_pipeline()
        JOBS[job_id]["status"] = "completed"
    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)


def get_job_status(job_id):
    return JOBS.get(job_id, {"status": "not_found"})

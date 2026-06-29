"""Integration test for the Flask REST API endpoints and backend services."""

import os
import tempfile
import pytest
from flask import Flask
from flask.testing import FlaskClient

from piracyguard.app import create_app
from piracyguard.config import settings
from piracyguard.database.session import session_scope, init_database, reset_engine
from piracyguard.database.models import User, UserRole
from piracyguard.services.auth_service import AuthService


@pytest.fixture
def app_instance():
    """Create a configured Flask application using a temporary SQLite database."""
    # Reset SQLAlchemy engine for clean isolation
    reset_engine()
    
    # Generate temporary database
    db_fd, db_path = tempfile.mkstemp()
    db_url = f"sqlite:///{db_path}"
    
    # Overwrite environment configuration URLs
    os.environ["DATABASE_URL"] = db_url
    os.environ["SECRET_KEY"] = "testing-secret-key-12345"
    os.environ["ADMIN_USERNAME"] = "admin"
    os.environ["ADMIN_PASSWORD"] = "admin"

    app = create_app(db_url)
    app.config["TESTING"] = True

    yield app

    # Cleanup database
    os.close(db_fd)
    os.unlink(db_path)
    reset_engine()


@pytest.fixture
def client(app_instance) -> FlaskClient:
    return app_instance.test_client()


def test_api_status(client):
    """Verify core root status endpoint works."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "online"
    assert "version" in data


def test_api_auth_and_restricted_access(client):
    """Verify JWT authentication and route protection work."""
    # 1. Accessing stats without token should fail with 401
    res = client.get("/api/v1/analytics/stats")
    assert res.status_code == 401

    # 2. Login with invalid credentials should fail
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"}
    )
    assert res.status_code == 401

    # 3. Login with correct credentials should succeed and return access token
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Access stats with valid token
    res = client.get("/api/v1/analytics/stats", headers=headers)
    assert res.status_code == 200
    stats = res.get_json()
    assert stats["status"] == "ACTIVE"
    assert stats["total_registered_videos"] == 0
    assert stats["total_scans"] == 0


def test_reference_registration_and_scan_endpoints(client):
    """Verify scan run, job status, and video registration work."""
    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    token = login_res.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create dummy reference file
    tmp_dir = tempfile.mkdtemp()
    dummy_video = os.path.join(tmp_dir, "ref_vid.mp4")
    
    # Write a simple file
    with open(dummy_video, "wb") as f:
        f.write(b"dummy video data")

    # Since the file is empty/invalid, registration might fail on frame extraction,
    # which raises a ProcessingError. Let's verify that the endpoint returns the correct
    # error response status code (e.g. 500 ProcessingError) when given invalid video.
    res = client.post(
        "/api/v1/scans/register",
        json={"video_path": dummy_video},
        headers=headers
    )
    assert res.status_code == 500  # FrameExtractionError -> ProcessingError -> 500
    
    # Enqueue a scan job (creates job and executes on uploads folder)
    res = client.post("/api/v1/scans/run", headers=headers)
    assert res.status_code == 202
    job_data = res.get_json()
    assert "job_id" in job_data
    job_uuid = job_data["job_id"]

    # Wait for the background job to complete (to release database locks before teardown)
    import time
    completed = False
    for _ in range(50):  # Max 5 seconds
        res = client.get(f"/api/v1/scans/job/{job_uuid}", headers=headers)
        assert res.status_code == 200
        status_data = res.get_json()
        if status_data["status"] in ("completed", "failed"):
            completed = True
            break
        time.sleep(0.1)

    assert completed
    assert status_data["uuid"] == job_uuid

import sqlite3
import os
from datetime import datetime

DB_PATH = "database/fingerprints.db"


def init_db():
    if not os.path.exists("database"):
        os.makedirs("database")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fingerprint Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_path TEXT UNIQUE,
            fingerprint TEXT
        )
    """)

    # Scan History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_path TEXT,
            similarity REAL,
            deepfake_score REAL,
            risk_score REAL,
            risk_level TEXT,
            scanned_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_fingerprint(video_path, fingerprint_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    fingerprint_str = "|".join(fingerprint_list)

    try:
        cursor.execute(
            "INSERT INTO fingerprints (video_path, fingerprint) VALUES (?, ?)",
            (video_path, fingerprint_str)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    conn.close()


def get_all_fingerprints():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT video_path, fingerprint FROM fingerprints")
    rows = cursor.fetchall()

    conn.close()

    result = {}
    for video_path, fingerprint_str in rows:
        result[video_path] = fingerprint_str.split("|")

    return result


# 🔥 NEW: Save Scan Result to History
def save_scan_history(result):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO scan_history
        (video_path, similarity, deepfake_score, risk_score, risk_level, scanned_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        result["video_path"],
        result["similarity"],
        result["deepfake_score"],
        result["risk_score"],
        result["risk_level"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_scan_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scan_history ORDER BY scanned_at DESC")
    rows = cursor.fetchall()

    conn.close()

    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "video_path": row[1],
            "similarity": row[2],
            "deepfake_score": row[3],
            "risk_score": row[4],
            "risk_level": row[5],
            "scanned_at": row[6]
        })

    return history

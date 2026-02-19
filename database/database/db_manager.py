import sqlite3
import os

DB_PATH = "database/fingerprints.db"


def init_db():
    if not os.path.exists("database"):
        os.makedirs("database")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_path TEXT UNIQUE,
            fingerprint TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_videos INTEGER,
            piracy_matches INTEGER,
            safe_videos INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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


def get_db_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM fingerprints")
    count = cursor.fetchone()[0]

    conn.close()

    return {
        "total_registered_videos": count
    }


def save_scan_history(total, piracy, safe):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO scan_history (total_videos, piracy_matches, safe_videos)
        VALUES (?, ?, ?)
    """, (total, piracy, safe))

    conn.commit()
    conn.close()


def get_scan_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, total_videos, piracy_matches, safe_videos, timestamp
        FROM scan_history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    history = []

    for row in rows:
        history.append({
            "id": row[0],
            "total_videos": row[1],
            "piracy_matches": row[2],
            "safe_videos": row[3],
            "timestamp": row[4]
        })

    return history


def get_trend_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, piracy_matches
        FROM scan_history
        ORDER BY timestamp ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    trend = []

    for row in rows:
        trend.append({
            "timestamp": row[0],
            "piracy_matches": row[1]
        })

    return trend

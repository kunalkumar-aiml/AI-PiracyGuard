import sqlite3
import os

DB_PATH = "database/fingerprints.db"


def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_path TEXT UNIQUE,
            fingerprint TEXT
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
        print("Fingerprint saved.")

    except sqlite3.IntegrityError:
        print("Fingerprint already exists for this video.")

    conn.close()


def get_all_fingerprints():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT video_path, fingerprint FROM fingerprints")
    rows = cursor.fetchall()

    conn.close()

    result = {}

    for video_path, fingerprint_str in rows:
        fingerprint_list = fingerprint_str.split("|")
        result[video_path] = fingerprint_list

    return result

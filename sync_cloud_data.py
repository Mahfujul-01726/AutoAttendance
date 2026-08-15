"""
AutoAttendance Cloud-to-Local Real-Time Sync Client.
Pulls real-time attendance logs, newly enrolled students, and Bayesian audit events
from your live Hugging Face Space (or any cloud URL) directly into your local PC's
SQLite database and Excel sheet.

Usage:
    python sync_cloud_data.py --url "https://your-huggingface-space-url"
"""

import os
import sys
import time
import argparse
import requests
import sqlite3
from pathlib import Path
from datetime import datetime

# Fix Windows console UTF-8 encoding
try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from auto_attendance.config import DATABASE_PATH, ATTENDANCE_DIR
from auto_attendance.database import AttendanceDatabase


def print_banner(title):
    print("\n" + "=" * 75)
    print(f"  🔄 {title}")
    print("=" * 75)


def sync_from_cloud(cloud_url: str):
    print_banner(f"SYNCING WITH CLOUD: {cloud_url}")
    
    cloud_url = cloud_url.rstrip("/")
    export_endpoint = f"{cloud_url}/api/export/json?days=365"

    print(f"[*] Fetching live attendance logs from: {export_endpoint} ...")
    try:
        response = requests.get(export_endpoint, timeout=15)
        if response.status_code != 200:
            print(f"[!] Server returned status {response.status_code}: {response.text}")
            return False
        
        records = response.json()
        print(f"[OK] Successfully fetched {len(records)} attendance records from Cloud!")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        print("Tip: Make sure your Hugging Face Space is running and the URL is correct.")
        return False

    # Connect to local SQLite database
    db = AttendanceDatabase()
    inserted_count = 0
    
    with db._connect() as conn:
        for r in records:
            name = r.get("name")
            date = r.get("date")
            time_str = r.get("time")
            distance = float(r.get("distance", 0.0))
            
            if not name or not date:
                continue

            # Check if record already exists locally
            existing = conn.execute(
                "SELECT id FROM attendance WHERE student_name = ? AND date = ?",
                (name, date)
            ).fetchone()

            if not existing:
                conn.execute(
                    """
                    INSERT INTO attendance (student_name, date, time, status, confidence, camera_id, created_at)
                    VALUES (?, ?, ?, 'Present', ?, 'Cloud-Web', ?)
                    """,
                    (name, date, time_str, distance, f"{date}T{time_str}")
                )
                inserted_count += 1

    print(f"[OK] Synced {inserted_count} new attendance records into local SQLite database!")
    print(f"📁 Local Database: {DATABASE_PATH}")
    print(f"📁 Local Attendance Dir: {ATTENDANCE_DIR}")

    # Generate updated summary
    print("\n[*] Running local longitudinal audit...")
    os.system(f'"{sys.executable}" generate_longitudinal_summary.py')

    return True


def run_continuous_sync(cloud_url: str, interval_seconds: int = 300):
    print_banner("AUTOATTENDANCE REAL-TIME CLOUD-SYNC DAEMON")
    print(f"  Cloud Space Target : {cloud_url}")
    print(f"  Sync Interval      : Every {interval_seconds} seconds (Press Ctrl+C to stop)")
    print("=" * 75 + "\n")

    while True:
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{now_str}] Starting sync pass...")
            sync_from_cloud(cloud_url)
            print(f"[*] Sleeping for {interval_seconds}s until next sync...")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n[!] Sync daemon stopped by user.")
            break
        except Exception as e:
            print(f"[!] Sync error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync live attendance from Hugging Face Space to local PC")
    parser.add_argument("--url", type=str, default="http://localhost:5000", help="Cloud space URL (e.g. https://your-space.hf.space)")
    parser.add_argument("--continuous", action="store_true", help="Run continuously every 5 minutes")
    parser.add_argument("--interval", type=int, default=300, help="Sync interval in seconds")

    args = parser.parse_args()

    if args.continuous:
        run_continuous_sync(args.url, args.interval)
    else:
        sync_from_cloud(args.url)

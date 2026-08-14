"""
System Reset & Data Cleanup Utility for AutoAttendance
Safely cleans old test data, dummy attendance logs, Excel sheets, and test faces.

Usage:
    python clean_system_data.py            # Interactive or full clean
    python clean_system_data.py --all      # Complete clean (wipes DB, logs, test faces)
    python clean_system_data.py --logs     # Cleans only attendance logs and history
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from auto_attendance.config import (
    ATTENDANCE_DIR,
    DATABASE_PATH,
    FACE_DATA_DIR,
    LOGS_DIR,
    UNKNOWN_FACES_DIR,
)
from auto_attendance.database import AttendanceDatabase


def print_banner(text: str):
    print("\n" + "=" * 65)
    print(f"  [*] {text}")
    print("=" * 65)


def clean_attendance_logs():
    """Remove old CSVs, Excel spreadsheets, and text logs."""
    print("[*] Cleaning old attendance logs and export files...")
    count = 0
    if ATTENDANCE_DIR.exists():
        for item in ATTENDANCE_DIR.iterdir():
            if item.is_file():
                try:
                    item.unlink()
                    count += 1
                except Exception as e:
                    print(f"    Could not remove {item.name}: {e}")

    # Root attendance log
    root_log = BASE_DIR / "attendance.log"
    if root_log.exists():
        try:
            root_log.unlink()
            count += 1
        except Exception:
            pass

    print(f"[OK] Cleaned {count} log/export files in data/attendance/")


def clean_unknown_faces():
    """Remove unknown face snapshots."""
    print("[*] Cleaning unknown face captures...")
    count = 0
    if UNKNOWN_FACES_DIR.exists():
        for item in UNKNOWN_FACES_DIR.iterdir():
            if item.is_file():
                try:
                    item.unlink()
                    count += 1
                except Exception:
                    pass
    print(f"[OK] Cleaned {count} unknown face snapshots")


def reset_database():
    """Wipe SQLite database and re-initialize fresh schema with UG-Adapt support."""
    print(f"[*] Resetting SQLite database at {DATABASE_PATH}...")
    if DATABASE_PATH.exists():
        try:
            DATABASE_PATH.unlink()
            print("[OK] Deleted old database file")
        except Exception as e:
            print(f"    Could not delete db file: {e}")

    # Re-initialize clean schema
    db = AttendanceDatabase(DATABASE_PATH)
    print("[OK] Fresh SQLite schema initialized successfully (Dual-Memory LTM/STM ready)")


def clean_test_faces():
    """Remove old dummy registered face image folders in data/faces/."""
    print("[*] Cleaning old test face folders in data/faces/...")
    count = 0
    if FACE_DATA_DIR.exists():
        for person_dir in FACE_DATA_DIR.iterdir():
            if person_dir.is_dir():
                try:
                    shutil.rmtree(person_dir)
                    print(f"    Removed test person: {person_dir.name}")
                    count += 1
                except Exception as e:
                    print(f"    Could not remove {person_dir.name}: {e}")
    print(f"[OK] Removed {count} old test face directories")


def main():
    parser = argparse.ArgumentParser(description="Clean old test data from AutoAttendance")
    parser.add_argument("--all", action="store_true", help="Perform full system reset (DB, logs, test faces)")
    parser.add_argument("--logs", action="store_true", help="Clean only attendance logs & history")
    parser.add_argument("--faces", action="store_true", help="Clean only registered face image folders")
    args = parser.parse_args()

    print_banner("AUTOATTENDANCE SYSTEM DATA CLEANUP & RESET")

    # Default to full clean if run without arguments
    full_reset = args.all or (not args.logs and not args.faces)

    if full_reset:
        clean_attendance_logs()
        clean_unknown_faces()
        clean_test_faces()
        reset_database()
        print_banner("FULL SYSTEM RESET COMPLETE - READY FOR REAL DATA ENROLLMENT")
        print("You can now enroll real faces:")
        print('  1. python -m auto_attendance.cli collect --name "YourName"')
        print("  2. python -m auto_attendance.cli train")
        print("  3. python -m auto_attendance.main\n")
    else:
        if args.logs:
            clean_attendance_logs()
            clean_unknown_faces()
            reset_database()
        if args.faces:
            clean_test_faces()


if __name__ == "__main__":
    main()

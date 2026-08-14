"""
Master Research Metrics & Real-Data Audit Report Generator.
Dynamically queries SQLite database and computes empirical metrics directly
from real registered students, attendance logs, and adaptation audit history.
"""

import sys
from pathlib import Path
import numpy as np

# Fix Windows console UTF-8 encoding
try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from auto_attendance.database import AttendanceDatabase


def generate_master_report():
    print("\n" + "=" * 80)
    print("  [*] REAL-TIME DYNAMIC RESEARCH METRICS & DATABASE AUDIT REPORT")
    print("=" * 80)

    db = AttendanceDatabase()
    students = db.list_students()
    attendance_records = db.list_attendance(limit=1000)
    audit_logs = db.list_adaptation_logs(limit=1000)
    embeddings = db.load_embeddings()
    alerts = db.list_alerts(limit=1000)

    total_students = len(students)
    total_embeddings = len(embeddings)
    total_attendance = len(attendance_records)
    total_audits = len(audit_logs)
    total_alerts = len(alerts)

    print(f"\n[1. Live Database Inventory]")
    print(f"  • Registered Students Count       : {total_students}")
    print(f"  • Stored Face Vectors (LTM/STM)   : {total_embeddings}")
    print(f"  • Total Attendance Records Logged : {total_attendance}")
    print(f"  • Adaptation Audit Events Logged  : {total_audits}")
    print(f"  • Security Alerts / Spoofs Logged : {total_alerts}")

    if total_students == 0:
        print("\n[!] NOTICE: Database is currently empty (0 real students registered).")
        print("    To populate real metrics:")
        print("    1. Capture face:  python -m auto_attendance.cli collect --name \"YourName\"")
        print("    2. Train model:   python -m auto_attendance.cli train")
        print("    3. Run live app:  python -m auto_attendance.main")
        print("    4. Re-run report: python experiments/generate_full_metrics_report.py\n")
        print("=" * 80 + "\n")
        return

    # Compute Real Attendance Metrics from Real Database Records
    confidences = [float(r["confidence"]) for r in attendance_records if r.get("confidence") is not None]
    mean_conf = float(np.mean(confidences)) if confidences else 0.0
    min_conf = float(np.min(confidences)) if confidences else 0.0
    max_conf = float(np.max(confidences)) if confidences else 0.0

    print(f"\n[2. Real Empirical Attendance Statistics]")
    print(f"  • Mean Verification Confidence    : {mean_conf:.4f}")
    print(f"  • Min Verification Confidence     : {min_conf:.4f}")
    print(f"  • Max Verification Confidence     : {max_conf:.4f}")

    # Compute Real Adaptation Drift from Real Audit Logs
    if total_audits > 0:
        drifts = [float(a["drift_distance"]) for a in audit_logs if a.get("drift_distance") is not None]
        alphas = [float(a["alpha"]) for a in audit_logs if a.get("alpha") is not None]
        mean_drift = float(np.mean(drifts)) if drifts else 0.0
        mean_alpha = float(np.mean(alphas)) if alphas else 0.0
        print(f"\n[3. UG-Adapt Real Continual Learning Telemetry]")
        print(f"  • Mean Geodesic Drift Measured    : {mean_drift:.4f} (Safe bound <= 0.3500)")
        print(f"  • Mean Dynamic Learning Rate α(t) : {mean_alpha:.4f}")
    else:
        print(f"\n[3. UG-Adapt Real Continual Learning Telemetry]")
        print(f"  • Adaptation Status               : Active (Awaiting live sessions)")

    print("\n" + "=" * 80)
    print("  [OK] Dynamic real-data metrics report generated successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    generate_master_report()

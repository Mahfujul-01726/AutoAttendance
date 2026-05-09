"""
Command-line interface for AutoAttendance system.
Provides a professional CLI with subcommands.
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

from logger import setup_logger, get_logger, log_system_event
from database import AttendanceDatabase
from face_recognition import FaceRecognitionModule
from config import (
    DATABASE_PATH,
    FACE_DATA_DIR,
    ATTENDANCE_DIR,
    MODELS_DIR,
    CAMERA_ID,
)

# Setup logger
setup_logger()
logger = get_logger()


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def cmd_collect(args) -> int:
    """Collect face samples for training."""
    from data_collection import DataCollectionModule
    
    print_header("Face Data Collection")
    
    collection = DataCollectionModule()
    person_name = args.name
    
    if not person_name:
        person_name = input(f"{Colors.CYAN}Enter person's name: {Colors.ENDC}").strip()
    
    if not person_name:
        print_error("Name cannot be empty")
        return 1
    
    num_samples = args.samples or 80
    print_info(f"Capturing {num_samples} samples for '{person_name}'...")
    
    collection.capture_face_samples(person_name, num_samples=num_samples, camera_id=CAMERA_ID)
    
    print_success(f"Data collection complete for {person_name}")
    log_system_event("info", "Face data collected", person=person_name, samples=num_samples)
    return 0


def cmd_train(args) -> int:
    """Train the face recognition model."""
    print_header("Model Training")
    
    recognizer = FaceRecognitionModule()
    
    print_info("Registering face embeddings...")
    people_count, embedding_count = recognizer.train_from_directory()
    
    if embedding_count == 0:
        print_error("No usable face images found!")
        print_info("Run 'python cli.py collect --name <name>' first")
        return 1
    
    print_success(f"Training complete!")
    print(f"  People registered: {Colors.GREEN}{people_count}{Colors.ENDC}")
    print(f"  Embeddings created: {Colors.GREEN}{embedding_count}{Colors.ENDC}")
    
    log_system_event("info", "Model trained", people=people_count, embeddings=embedding_count)
    return 0


def cmd_run(args) -> int:
    """Run the attendance system."""
    from main import AttendanceSystem
    
    print_header("Starting Attendance System")
    
    system = AttendanceSystem()
    
    print_info("Press 'q' to quit, 's' to export report")
    print_info(f"Camera ID: {CAMERA_ID}")
    print_info(f"Database: {DATABASE_PATH}")
    
    system.run()
    
    print_success("System shutdown complete")
    log_system_event("info", "System stopped")
    return 0


def cmd_status(args) -> int:
    """Show system status and statistics."""
    print_header("System Status")
    
    db = AttendanceDatabase()
    
    # Student statistics
    students = db.list_students()
    print(f"{Colors.BOLD}Students:{Colors.ENDC} {len(students)}")
    
    for student in students:
        name = student.get("name", "Unknown")
        embeddings = student.get("embedding_count", 0)
        status = student.get("status", "unknown")
        status_color = Colors.GREEN if status == "active" else Colors.WARNING
        print(f"  • {name}: {embeddings} embeddings [{status_color}{status}{Colors.ENDC}]")
    
    # Today's attendance
    today = datetime.now().strftime("%Y-%m-%d")
    attendance = db.list_attendance(date=today, limit=1000)
    print(f"\n{Colors.BOLD}Today's Attendance ({today}):{Colors.ENDC} {len(attendance)}")
    
    for record in attendance:
        name = record.get("student_name", "Unknown")
        time = record.get("time", "N/A")
        print(f"  • {name} at {time}")
    
    # Recent alerts
    alerts = db.list_alerts(limit=5)
    print(f"\n{Colors.BOLD}Recent Alerts:{Colors.ENDC} {len(alerts)}")
    
    if alerts:
        for alert in alerts:
            alert_type = alert.get("alert_type", "unknown")
            message = alert.get("message", "")[:50]
            created = alert.get("created_at", "")[:19]
            print(f"  • [{alert_type}] {message}... ({created})")
    else:
        print("  No recent alerts")
    
    # Storage info
    db_path = Path(DATABASE_PATH)
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"\n{Colors.BOLD}Database Size:{Colors.ENDC} {size_mb:.2f} MB")
    
    log_system_event("info", "Status checked")
    return 0


def cmd_export(args) -> int:
    """Export attendance data."""
    print_header("Exporting Attendance Data")
    
    db = AttendanceDatabase()
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    
    attendance = db.list_attendance(date=date, limit=10000)
    
    if not attendance:
        print_warning(f"No attendance records for {date}")
        return 1
    
    # Export to CSV
    import pandas as pd
    output_dir = Path(ATTENDANCE_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"attendance_export_{date}.csv"
    filepath = output_dir / filename
    
    df = pd.DataFrame(attendance)
    df.to_csv(filepath, index=False)
    
    print_success(f"Exported {len(attendance)} records")
    print(f"  File: {filepath}")
    
    log_system_event("info", "Attendance exported", date=date, records=len(attendance))
    return 0


def cmd_api(args) -> int:
    """Start the API server."""
    import uvicorn
    
    print_header("Starting API Server")
    
    host = args.host or "0.0.0.0"
    port = args.port or 8000
    
    print_info(f"Server starting at http://{host}:{port}")
    print_info("Dashboard: http://localhost:8000/")
    print_info("API docs: http://localhost:8000/docs")
    print_info("Press Ctrl+C to stop")
    
    log_system_event("info", "API server starting", host=host, port=port)
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=args.reload,
        log_level="info"
    )
    
    return 0


def cmd_setup(args) -> int:
    """Run system setup wizard."""
    import subprocess
    
    print_header("Running Setup")
    
    try:
        result = subprocess.run([sys.executable, "setup.py"], capture_output=False)
        return result.returncode
    except Exception as e:
        print_error(f"Setup failed: {e}")
        return 1


def cmd_test(args) -> int:
    """Run system diagnostics."""
    print_header("System Diagnostics")
    
    errors = []
    warnings = []
    
    # Check Python version
    print_info("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        errors.append("Python 3.8+ required")
    else:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    
    # Check dependencies
    print_info("Checking dependencies...")
    required = {
        "cv2": "opencv-python",
        "numpy": "numpy",
        "pandas": "pandas",
        "insightface": "insightface",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
    }
    
    for import_name, package_name in required.items():
        try:
            __import__(import_name)
            print_success(f"{package_name}")
        except ImportError:
            errors.append(f"{package_name} not installed")
            print_error(f"{package_name} NOT installed")
    
    # Check directories
    print_info("Checking directories...")
    dirs = [
        ("data/faces", "Face data"),
        ("data/attendance", "Attendance records"),
        ("models", "Model storage"),
    ]
    
    for path, desc in dirs:
        if os.path.isdir(path):
            print_success(f"{desc}: {path}")
        else:
            warnings.append(f"{desc} directory missing: {path}")
            print_warning(f"{desc}: {path} (missing)")
    
    # Check database
    print_info("Checking database...")
    db_path = Path(DATABASE_PATH)
    if db_path.exists():
        print_success(f"Database exists: {db_path}")
        
        db = AttendanceDatabase()
        students = db.list_students()
        print(f"  {len(students)} registered students")
    else:
        warnings.append("Database not initialized")
        print_warning("Database not initialized (run 'python train_model.py')")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"{Colors.RED}Errors: {len(errors)}{Colors.ENDC}")
        for e in errors:
            print(f"  • {e}")
    
    if warnings:
        print(f"{Colors.WARNING}Warnings: {len(warnings)}{Colors.ENDC}")
        for w in warnings:
            print(f"  • {w}")
    
    if not errors and not warnings:
        print_success("All checks passed!")
        return 0
    elif not errors:
        return 0
    else:
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="autoattendance",
        description="Face Recognition Attendance System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py status              Show system status
  python cli.py collect --name John Collect face data
  python cli.py train              Train the model
  python cli.py run                Start attendance system
  python cli.py api                Start API server
  python cli.py test               Run diagnostics
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect face samples")
    collect_parser.add_argument("--name", "-n", help="Person's name")
    collect_parser.add_argument("--samples", "-s", type=int, help="Number of samples (default: 80)")
    collect_parser.set_defaults(func=cmd_collect)
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train face recognition model")
    train_parser.set_defaults(func=cmd_train)
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the attendance system")
    run_parser.set_defaults(func=cmd_run)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.set_defaults(func=cmd_status)
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export attendance data")
    export_parser.add_argument("--date", "-d", help="Date (YYYY-MM-DD, default: today)")
    export_parser.set_defaults(func=cmd_export)
    
    # API command
    api_parser = subparsers.add_parser("api", help="Start API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host address")
    api_parser.add_argument("--port", "-p", type=int, default=8000, help="Port number")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    api_parser.set_defaults(func=cmd_api)
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Run setup wizard")
    setup_parser.set_defaults(func=cmd_setup)
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run system diagnostics")
    test_parser.set_defaults(func=cmd_test)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print_error(f"Error: {e}")
        logger.exception("CLI error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
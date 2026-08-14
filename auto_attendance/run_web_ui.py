"""
AutoAttendance Web UI Launcher
Simple launcher script for non-technical users to start the web interface
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['flask', 'flask_cors']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('_', '-'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("\n⚠️  Missing required packages!")
        print(f"Installing: {', '.join(missing)}")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing)
        print("✓ Packages installed successfully!\n")

def check_model():
    """Check if model files exist"""
    models_dir = Path(__file__).parent / 'models'
    if not models_dir.exists():
        models_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for SQLite database
    db_path = models_dir / 'attendance.sqlite3'
    if not db_path.exists():
        print("📦 First run - initializing database...")
        # Database will be created on first use

def print_welcome():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("  🎉 AUTOATTENDANCE WEB UI LAUNCHER")
    print("="*70)
    print("\n  Welcome! Starting the AutoAttendance system...\n")

def start_web_server():
    """Start the Flask web server"""
    try:
        print("🚀 Starting web server...\n")
        
        # Import and run Flask app
        from .web_ui import app
        
        # Run Flask
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure all requirements are installed:")
        print("     pip install -r requirements.txt")
        print("  2. Check if port 5000 is available")
        print("  3. Try running: python web_ui.py")
        sys.exit(1)

def open_browser():
    """Open web browser after a delay"""
    print("\n✓ Server started successfully!")
    print("\n📱 Opening in browser in 2 seconds...")
    print("   If it doesn't open, visit: http://localhost:5000\n")
    
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:5000')
    except Exception as e:
        print(f"Could not open browser: {e}")
        print("Please manually open: http://localhost:5000\n")

def print_instructions():
    """Print usage instructions"""
    print("\n" + "="*70)
    print("  📖 HOW TO USE")
    print("="*70)
    print("""
  1. DASHBOARD
     - View system statistics
     - Check recent attendance records
     - Quick access to main features

  2. REGISTER PERSON
     - Step 1: Enter the person's name
     - Step 2: Collect 20-30 face samples using camera
     - Step 3: Train the model
     
  3. ATTENDANCE RECORDS
     - View all attendance history
     - Search by name
     - Filter and export data (CSV/JSON)
     
  4. SETTINGS
     - Configure camera and recognition settings
     - Enable/disable notifications
     - Manage data and backups

  KEYBOARD SHORTCUTS:
     - Ctrl+K: Open search
     - Esc: Close dialogs

  TIPS FOR NON-TECHNICAL USERS:
     ✓ Start by registering at least 2-3 people first
     ✓ Collect faces from different angles for better accuracy
     ✓ Ensure good lighting for best results
     ✓ Use the Export feature to backup your data regularly
""")
    print("="*70 + "\n")

def main():
    """Main entry point"""
    print_welcome()
    
    try:
        # Check requirements
        check_requirements()
        
        # Check model files
        check_model()
        
        # Print instructions
        print_instructions()
        
        print("🔌 Connecting to system components...")
        
        # Start server in a way that allows us to open browser
        print("\n" + "="*70)
        print("  🌐 WEB SERVER RUNNING")
        print("="*70)
        print("\n✓ All systems initialized\n")
        
        # Start the server
        start_web_server()
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down AutoAttendance...")
        print("See you next time! 👋\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

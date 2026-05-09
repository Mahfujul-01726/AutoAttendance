#!/bin/bash
# AutoAttendance Web UI Launcher for macOS and Linux

echo ""
echo "========================================================================"
echo "  AutoAttendance Web UI Launcher"
echo "========================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.9+ using:"
    echo "  macOS: brew install python3"
    echo "  Linux: apt-get install python3 python3-pip"
    exit 1
fi

# Install requirements if needed
echo "Checking dependencies..."
python3 -m pip install -q flask flask-cors 2>/dev/null

# Start the web UI
echo ""
echo "Starting AutoAttendance Web UI..."
echo ""

python3 run_web_ui.py

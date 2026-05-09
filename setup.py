"""
Quick Start Guide - Run this first!
Sets up the project and guides you through initial steps
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if all required packages are installed"""
    print("=" * 60)
    print("CHECKING DEPENDENCIES")
    print("=" * 60)
    
    required_packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'PIL': 'Pillow',
        'dotenv': 'python-dotenv',
        'insightface': 'insightface',
        'onnxruntime': 'onnxruntime',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn'
    }
    
    missing = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name} is installed")
        except ImportError:
            print(f"✗ {package_name} is NOT installed")
            missing.append(package_name)
    
    if missing:
        print("\nInstalling missing packages...")
        cmd = f"pip install {' '.join(missing)}"
        subprocess.run(cmd, shell=True)
        print("Installation complete!")
    
    return len(missing) == 0

def setup_directories():
    """Create necessary directories"""
    print("\n" + "=" * 60)
    print("SETTING UP DIRECTORIES")
    print("=" * 60)
    
    directories = [
        'data',
        'data/faces',
        'data/training',
        'data/attendance',
        'data/unknown_faces',
        'models'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created/verified: {directory}")

def setup_env_file():
    """Setup .env file"""
    print("\n" + "=" * 60)
    print("SETTING UP ENVIRONMENT FILE")
    print("=" * 60)
    
    if os.path.exists('.env'):
        print("✓ .env file already exists")
        return
    
    if os.path.exists('.env.example'):
        with open('.env.example', 'r') as f:
            content = f.read()
        
        with open('.env', 'w') as f:
            f.write(content)
        
        print("✓ Created .env from template")
    else:
        print("ℹ️  .env.example not found (not required)")

def show_next_steps():
    """Display next steps"""
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    print("""
1. COLLECT TRAINING DATA:
   python data_collection.py
   
   - Enter person's name when prompted
   - Position face in front of camera
   - Press 'c' to capture, 'q' to finish
   - Collect at least 80 samples per person
   
2. TRAIN THE MODEL:
   python train_model.py
   
   - Takes a few minutes depending on data size
   - Registers InsightFace embeddings in models/attendance.sqlite3
   
3. RUN THE ATTENDANCE SYSTEM:
   python main.py
   
   - Press 'q' to quit
   - Press 's' to export attendance report
   
4. CHECK RESULTS:
   - Attendance records saved in: data/attendance/
   - Excel file: data/attendance/attendance.xlsx
   - Log file: attendance.log

TIPS:
- Collect faces at different angles and lighting
- Use a well-lit environment
- Ensure camera is working before starting
- Position face 20-50cm from camera for best results
""")

def test_camera():
    """Test if camera is working"""
    print("\n" + "=" * 60)
    print("TESTING CAMERA")
    print("=" * 60)
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print("✓ Camera is working!")
            
            ret, frame = cap.read()
            if ret:
                print(f"✓ Frame captured: {frame.shape}")
            
            cap.release()
        else:
            print("✗ Camera not detected!")
            print("  Try changing CAMERA_ID in config.py")
    
    except Exception as e:
        print(f"✗ Error testing camera: {e}")

def main():
    """Main setup wizard"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  FACE RECOGNITION ATTENDANCE SYSTEM - SETUP WIZARD".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️  Some dependencies could not be installed")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    
    # Setup environment
    setup_env_file()
    
    # Test camera
    test_camera()
    
    # Show next steps
    show_next_steps()
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE! ✓")
    print("=" * 60)
    print("\nFor detailed information, see SETUP_GUIDE.md")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Diagnostic script to identify system components, camera access, and embeddings.
"""

import sys
from pathlib import Path
import cv2
import numpy as np

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.absolute()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from .config import FACE_DATA_DIR, DATABASE_PATH, CAMERA_ID
    from .database import AttendanceDatabase
    from .face_recognition import FaceRecognitionModule
    from .logger import get_logger
except (ImportError, ValueError):
    from auto_attendance.config import FACE_DATA_DIR, DATABASE_PATH, CAMERA_ID
    from auto_attendance.database import AttendanceDatabase
    from auto_attendance.face_recognition import FaceRecognitionModule
    from auto_attendance.logger import get_logger

logger = get_logger()


def check_face_data():
    """Check if face data exists and is properly organized."""
    print("\n" + "="*60)
    print("1. CHECKING FACE DATA")
    print("="*60)
    
    if not FACE_DATA_DIR.exists():
        print(f"[FAIL] Face data directory not found: {FACE_DATA_DIR}")
        return False
    
    print(f"[OK] Face data directory found: {FACE_DATA_DIR}")
    
    total_images = 0
    for person_dir in FACE_DATA_DIR.iterdir():
        if person_dir.is_dir():
            images = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
            total_images += len(images)
            print(f"  - {person_dir.name}: {len(images)} images")
    
    if total_images == 0:
        print("[INFO] No raw face images found in data/faces/. (Embeddings may already be in database)")
        return True
    
    print(f"[OK] Total face images: {total_images}")
    return True


def check_embeddings():
    """Check if embeddings are loaded in database."""
    print("\n" + "="*60)
    print("2. CHECKING EMBEDDINGS IN DATABASE")
    print("="*60)
    
    try:
        db = AttendanceDatabase(str(DATABASE_PATH))
        embeddings = db.load_embeddings()
        
        if not embeddings:
            print(f"[WARNING] No embeddings found in database: {DATABASE_PATH}")
            print("   You need to enroll faces first via CLI or Web UI.")
            return False
        
        print(f"[OK] Database found: {DATABASE_PATH}")
        print(f"[OK] Loaded {len(embeddings)} embeddings")
        
        people_embeddings = {}
        for emb in embeddings:
            name = emb.get('student_name', 'Unknown')
            people_embeddings[name] = people_embeddings.get(name, 0) + 1
        
        for name, count in sorted(people_embeddings.items()):
            print(f"  - {name}: {count} embeddings")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error checking embeddings: {e}")
        return False


def check_model():
    """Check if model can be loaded."""
    print("\n" + "="*60)
    print("3. CHECKING FACE RECOGNITION MODEL")
    print("="*60)
    
    try:
        recognizer = FaceRecognitionModule()
        recognizer.load_model()
        print("[OK] Face recognition model loaded successfully")
        print(f"  - Model: {recognizer.model_name}")
        print(f"  - Known embeddings: {recognizer.label_count}")
        return True
    except Exception as e:
        print(f"[FAIL] Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_camera():
    """Check if camera can be accessed."""
    print("\n" + "="*60)
    print("4. CHECKING CAMERA")
    print("="*60)
    
    try:
        cap = cv2.VideoCapture(CAMERA_ID)
        if not cap.isOpened():
            print(f"[WARNING] Cannot open camera (ID: {CAMERA_ID})")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Cannot read frames from camera")
            cap.release()
            return False
        
        print(f"[OK] Camera opened successfully (ID: {CAMERA_ID})")
        print(f"  - Frame size: {frame.shape}")
        cap.release()
        return True
    except Exception as e:
        print(f"[FAIL] Error accessing camera: {e}")
        return False


def test_face_detection():
    """Test face detection on a sample image or camera frame."""
    print("\n" + "="*60)
    print("5. TESTING FACE DETECTION")
    print("="*60)
    
    try:
        recognizer = FaceRecognitionModule()
        
        cap = cv2.VideoCapture(CAMERA_ID)
        if not cap.isOpened():
            print("[WARNING] Camera not available for live detection test")
            return True
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            print("[WARNING] Could not grab test frame")
            return True
        
        faces = recognizer.detect_faces(frame)
        print(f"[OK] Faces detected in test frame: {len(faces)}")
        
        for i, face in enumerate(faces):
            print(f"  - Face {i+1}: det_score={float(getattr(face, 'det_score', 0)):.3f}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error testing face detection: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic checks."""
    print("\n" + "="*60)
    print("  AUTOATTENDANCE DIAGNOSTICS")
    print("="*60)
    
    results = {
        "Face Data": check_face_data(),
        "Embeddings": check_embeddings(),
        "Model": check_model(),
        "Camera": check_camera(),
        "Face Detection": test_face_detection(),
    }
    
    print("\n" + "="*60)
    print("  DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:8}: {check}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Diagnostic script to identify why face detection is not working.
"""

import sys
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import FACE_DATA_DIR, DATABASE_PATH, CAMERA_ID
from database import AttendanceDatabase
from face_recognition import FaceRecognitionModule
from logger import get_logger

logger = get_logger()

def check_face_data():
    """Check if face data exists and is properly organized."""
    print("\n" + "="*60)
    print("1. CHECKING FACE DATA")
    print("="*60)
    
    if not FACE_DATA_DIR.exists():
        print(f"❌ Face data directory not found: {FACE_DATA_DIR}")
        return False
    
    print(f"✓ Face data directory found: {FACE_DATA_DIR}")
    
    total_images = 0
    for person_dir in FACE_DATA_DIR.iterdir():
        if person_dir.is_dir():
            images = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
            total_images += len(images)
            print(f"  - {person_dir.name}: {len(images)} images")
    
    if total_images == 0:
        print("❌ No face images found! You need to register faces first.")
        return False
    
    print(f"✓ Total face images: {total_images}")
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
            print(f"❌ No embeddings found in database: {DATABASE_PATH}")
            print("   You need to run: python train_model.py")
            return False
        
        print(f"✓ Database found: {DATABASE_PATH}")
        print(f"✓ Loaded {len(embeddings)} embeddings")
        
        # Show breakdown by person
        people_embeddings = {}
        for emb in embeddings:
            name = emb.get('student_name', 'Unknown')
            people_embeddings[name] = people_embeddings.get(name, 0) + 1
        
        for name, count in sorted(people_embeddings.items()):
            print(f"  - {name}: {count} embeddings")
        
        return True
    except Exception as e:
        print(f"❌ Error checking embeddings: {e}")
        return False


def check_model():
    """Check if model can be loaded."""
    print("\n" + "="*60)
    print("3. CHECKING FACE RECOGNITION MODEL")
    print("="*60)
    
    try:
        recognizer = FaceRecognitionModule()
        recognizer.load_model()
        print("✓ Face recognition model loaded successfully")
        print(f"  - Model: {recognizer.model_name}")
        print(f"  - Known embeddings: {recognizer.label_count}")
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
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
            print(f"❌ Cannot open camera (ID: {CAMERA_ID})")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print(f"❌ Cannot read frames from camera")
            cap.release()
            return False
        
        print(f"✓ Camera opened successfully (ID: {CAMERA_ID})")
        print(f"  - Frame size: {frame.shape}")
        cap.release()
        return True
    except Exception as e:
        print(f"❌ Error accessing camera: {e}")
        return False


def test_face_detection():
    """Test face detection on a sample image."""
    print("\n" + "="*60)
    print("5. TESTING FACE DETECTION")
    print("="*60)
    
    try:
        recognizer = FaceRecognitionModule()
        
        # Try detecting from camera
        cap = cv2.VideoCapture(CAMERA_ID)
        if not cap.isOpened():
            print("❌ Cannot open camera for testing")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("❌ Cannot read frame from camera")
            return False
        
        # Detect faces
        faces = recognizer.detect_faces(frame)
        print(f"✓ Faces detected in camera frame: {len(faces)}")
        
        if len(faces) == 0:
            print("  ⚠️  No faces detected - check camera angle, lighting, and distance")
            return False
        
        for i, face in enumerate(faces):
            print(f"  - Face {i+1}: conf={float(getattr(face, 'det_score', 0)):.3f}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing face detection: {e}")
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
    
    # Summary
    print("\n" + "="*60)
    print("  DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")
    
    print("\n" + "="*60)
    if all(results.values()):
        print("✓ All checks passed! System should work.")
    else:
        print("❌ Some checks failed. See details above.")
        print("\nQuick fixes:")
        if not results["Face Data"]:
            print("  1. Register face images: python train_model.py")
        if not results["Embeddings"]:
            print("  2. Train embeddings: python train_model.py")
        if not results["Face Detection"]:
            print("  3. Check camera: angle, lighting, distance from camera")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

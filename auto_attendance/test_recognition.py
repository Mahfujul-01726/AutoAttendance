"""
Test script to verify InsightFace cosine-distance scores.
"""

import os
import sys
from pathlib import Path
import cv2

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.absolute()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from .config import FACE_DATA_DIR, RECOGNITION_THRESHOLD
    from .face_recognition import FaceRecognitionModule
except (ImportError, ValueError):
    from auto_attendance.config import FACE_DATA_DIR, RECOGNITION_THRESHOLD
    from auto_attendance.face_recognition import FaceRecognitionModule


def test_recognition():
    recognizer = FaceRecognitionModule()
    recognizer.load_model()

    print("\n" + "=" * 60)
    print("TESTING FACE RECOGNITION DISTANCE SCORES")
    print("=" * 60)
    print(f"Recognition distance threshold: {RECOGNITION_THRESHOLD}")
    print(f"Distances <= {RECOGNITION_THRESHOLD} = recognized")
    print(f"Distances >  {RECOGNITION_THRESHOLD} = unknown\n")

    if not os.path.exists(FACE_DATA_DIR):
        print(f"Face data directory not found: {FACE_DATA_DIR}")
        return

    tested = 0
    for person_name in sorted(os.listdir(FACE_DATA_DIR)):
        person_path = os.path.join(FACE_DATA_DIR, person_name)
        if not os.path.isdir(person_path):
            continue

        images = os.listdir(person_path)
        if not images:
            continue

        image_path = os.path.join(person_path, images[0])
        face_image = cv2.imread(image_path)

        if face_image is not None:
            label, confidence = recognizer.recognize_face(face_image)
            recognized_name = recognizer.get_person_name(label)
            is_known = recognizer.is_known_person(confidence)

            status = "RECOGNIZED" if is_known else "UNKNOWN"
            print(f"{person_name:15} -> {recognized_name:15} (distance: {confidence:6.3f}) {status}")
            tested += 1

    if tested == 0:
        print("No face folders found to test. Enroll faces first.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_recognition()

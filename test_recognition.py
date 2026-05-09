"""
Test script to verify InsightFace cosine-distance scores.
Run this after python train_model.py.
"""

import cv2
import os
from face_recognition import FaceRecognitionModule
from config import FACE_DATA_DIR, RECOGNITION_THRESHOLD

recognizer = FaceRecognitionModule()
recognizer.load_model()

print("\n" + "=" * 60)
print("TESTING FACE RECOGNITION DISTANCE SCORES")
print("=" * 60)
print(f"Recognition distance threshold: {RECOGNITION_THRESHOLD}")
print(f"Distances <= {RECOGNITION_THRESHOLD} = recognized")
print(f"Distances >  {RECOGNITION_THRESHOLD} = unknown\n")

for person_name in os.listdir(FACE_DATA_DIR):
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

print("\n" + "=" * 60)
print("If expected people show RECOGNIZED, run: python main.py")
print("=" * 60)

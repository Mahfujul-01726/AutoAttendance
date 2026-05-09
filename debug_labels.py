"""
Debug script to check which registered student each sample matches.
"""

import cv2
import os
from config import FACE_DATA_DIR

recognizer = __import__("face_recognition").FaceRecognitionModule()
recognizer.load_model()

print("\n" + "=" * 60)
print("CHECKING ACTUAL MATCHES FOR EACH PERSON")
print("=" * 60)

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

        match = "MATCH" if person_name == recognized_name else "MISMATCH"
        print(f"\nPerson: {person_name}")
        print(f"  Detected as: {recognized_name} (student_id={label}, distance={confidence:.3f}) {match}")

print("\n" + "=" * 60)
print("If there is a MISMATCH, collect more samples or tune RECOGNITION_THRESHOLD.")
print("=" * 60)

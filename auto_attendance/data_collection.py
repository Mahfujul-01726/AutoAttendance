import cv2
import os
from .config import CAMERA_ID, FACE_DATA_DIR, FRAME_HEIGHT, FRAME_WIDTH, TRAINING_DATA_DIR
from .face_recognition import FaceRecognitionModule


class DataCollectionModule:
    """Collects face samples for InsightFace embedding registration."""

    def __init__(self):
        os.makedirs(FACE_DATA_DIR, exist_ok=True)
        os.makedirs(TRAINING_DATA_DIR, exist_ok=True)
        self.face_detector = FaceRecognitionModule()

    def capture_face_samples(self, person_name, num_samples=80, camera_id=CAMERA_ID):
        """
        Capture face samples from camera.

        Args:
            person_name: Name of the person.
            num_samples: Number of samples to capture.
            camera_id: Camera device ID.
        """
        person_dir = os.path.join(FACE_DATA_DIR, person_name)
        os.makedirs(person_dir, exist_ok=True)

        cap = cv2.VideoCapture(camera_id)

        if not cap.isOpened():
            print("Error: Cannot open camera")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        print(f"Capturing {num_samples} samples for {person_name}...")
        print("IMPORTANT: Capture faces at DIFFERENT ANGLES for better recognition!")
        print("Press 'q' to skip, 'c' to capture frame")
        print("\nTip: Move your head at different angles:")
        print("  - Straight ahead")
        print("  - Turn left 20-30 degrees")
        print("  - Turn right 20-30 degrees")
        print("  - Tilt up slightly")
        print("  - Tilt down slightly")
        print("  - Different lighting conditions")
        print("=" * 60)

        count = 0

        while count < num_samples:
            ret, frame = cap.read()

            if not ret:
                print("Failed to read frame")
                break

            faces = self.face_detector.detect_faces(frame)
            frame_display = self.face_detector.draw_faces(frame, faces)

            cv2.putText(frame_display, f"Samples: {count}/{num_samples}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame_display, "VARY ANGLES! Press 'c' to capture or 'q' to quit", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame_display, "Angle variation is key for robust recognition", (10, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            cv2.imshow(f"Capturing faces for {person_name}", frame_display)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print(f"Skipping {person_name}")
                break
            elif key == ord('c'):
                if len(faces) > 0:
                    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                    face_roi = self.face_detector.extract_face_roi(frame, face)

                    if face_roi.size == 0:
                        print("Detected face crop is empty")
                        continue

                    face_roi = cv2.resize(face_roi, (224, 224))
                    filename = os.path.join(person_dir, f"{person_name}_{count}.jpg")
                    cv2.imwrite(filename, face_roi)
                    print(f"Saved: {filename}")

                    count += 1
                else:
                    print("No face detected in current frame")

        cap.release()
        cv2.destroyAllWindows()

        print(f"Captured {count} samples for {person_name}")

    def prepare_training_data(self):
        """
        Count collected images for user feedback.

        Returns:
            (faces_list, labels_list, labels_dict), kept for script compatibility.
        """
        faces_list = []
        labels_list = []
        labels_dict = {}
        label_count = 0

        print("Preparing training data...")

        for person_name in sorted(os.listdir(FACE_DATA_DIR)):
            person_path = os.path.join(FACE_DATA_DIR, person_name)

            if not os.path.isdir(person_path):
                continue

            labels_dict[label_count] = person_name
            print(f"Processing {person_name}...")

            for image_name in sorted(os.listdir(person_path)):
                image_path = os.path.join(person_path, image_name)
                face_image = cv2.imread(image_path)

                if face_image is not None:
                    faces_list.append(face_image)
                    labels_list.append(label_count)

            label_count += 1

        print(f"Prepared {len(faces_list)} faces for {label_count} people")
        return faces_list, labels_list, labels_dict


def main():
    """Main script for data collection."""
    collection = DataCollectionModule()

    print("\n" + "=" * 60)
    print("FACE DATA COLLECTION SYSTEM")
    print("=" * 60)

    people = []

    while True:
        person_name = input("\nEnter person's name (or 'done' to finish): ").strip()

        if person_name.lower() == 'done':
            if len(people) == 0:
                print("Please enter at least one person's name!")
                continue
            break

        if not person_name:
            print("Please enter a valid name!")
            continue

        people.append(person_name)
        print(f"Added: {person_name}")

    print(f"\n\nCollecting faces for {len(people)} people: {people}")
    print("=" * 60)

    for person in people:
        num_samples = input(f"\nNumber of samples for {person} (default 80): ").strip()

        try:
            num_samples = int(num_samples) if num_samples else 80
        except ValueError:
            num_samples = 80

        collection.capture_face_samples(person, num_samples=num_samples)

    print("\n\nPreparing training data...")
    faces, labels, labels_dict = collection.prepare_training_data()

    print("\n" + "=" * 60)
    print(f"Total faces collected: {len(faces)}")
    print(f"Labels: {labels_dict}")
    print("=" * 60)
    print("\nNext step: python train_model.py")


if __name__ == "__main__":
    main()

import os
import warnings

import cv2
import numpy as np

from config import (
    DATABASE_PATH,
    FACE_DATA_DIR,
    INSIGHTFACE_DET_SIZE,
    INSIGHTFACE_MAX_FACES,
    INSIGHTFACE_MODEL_NAME,
    INSIGHTFACE_PROVIDERS,
    RECOGNITION_THRESHOLD,
)
from database import AttendanceDatabase

warnings.filterwarnings(
    "ignore",
    message="`estimate` is deprecated.*",
    category=FutureWarning,
    module="insightface.utils.face_align",
)


class FaceRecognitionModule:
    """Face detection and recognition using pretrained InsightFace embeddings."""

    def __init__(self, db_path=DATABASE_PATH):
        self.db = AttendanceDatabase(db_path)
        self.model_name = INSIGHTFACE_MODEL_NAME
        self.app = self._load_insightface()
        self.known_embeddings = []
        self.labels = {}
        self.reverse_labels = {}
        self.label_count = 0

    def _load_insightface(self):
        try:
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise ImportError(
                "InsightFace is required for the upgraded recognition engine. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from exc

        app = FaceAnalysis(name=INSIGHTFACE_MODEL_NAME, providers=INSIGHTFACE_PROVIDERS)
        app.prepare(ctx_id=-1, det_size=INSIGHTFACE_DET_SIZE)
        return app

    def load_model(self):
        """Load registered embeddings from SQLite."""
        self.known_embeddings = self.db.load_embeddings()
        self.reverse_labels = {
            item["student_id"]: item["student_name"] for item in self.known_embeddings
        }
        self.labels = {name: label for label, name in self.reverse_labels.items()}
        self.label_count = len(self.reverse_labels)

        if not self.known_embeddings:
            print("No face embeddings found. Register faces first using train_model.py")
            return

        print(f"Loaded {len(self.known_embeddings)} face embeddings from {self.db.db_path}")

    def detect_faces(self, frame, max_num=INSIGHTFACE_MAX_FACES):
        """Detect faces and compute embeddings for a BGR frame."""
        return self.app.get(frame, max_num=max_num)

    def draw_faces(self, frame, faces, color=(0, 255, 0), thickness=2):
        frame_copy = frame.copy()
        for face in faces:
            x1, y1, x2, y2 = self._bbox_to_int(face.bbox, frame.shape)
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, thickness)
        return frame_copy

    def extract_face_roi(self, frame, face):
        x1, y1, x2, y2 = self._bbox_to_int(face.bbox, frame.shape)
        return frame[y1:y2, x1:x2]

    def train_recognizer(self, faces_list, labels_list):
        """
        Register embeddings from existing face images.

        This keeps backward compatibility with the old LBPH training script:
        labels_list maps each image to self.reverse_labels[label].
        """
        if not faces_list:
            raise ValueError("No training data provided")

        self.db.clear_embeddings()
        saved_count = 0

        for image, label in zip(faces_list, labels_list):
            person_name = self.reverse_labels.get(label)
            if not person_name:
                continue

            student_id = self.db.upsert_student(person_name)
            embedding, quality_score = self._embedding_from_image(image)
            if embedding is None:
                print(f"Skipped one image for {person_name}: no face detected")
                continue

            self.db.add_embedding(
                student_id,
                embedding,
                model_name=self.model_name,
                quality_score=quality_score,
            )
            saved_count += 1

        self.load_model()
        print(f"Registered {saved_count} embeddings in {self.db.db_path}")

    def train_from_directory(self, face_data_dir=FACE_DATA_DIR):
        """Register all images from data/faces/<person_name>/ into SQLite."""
        if not os.path.isdir(face_data_dir):
            raise ValueError(f"Training data folder not found: {face_data_dir}")

        self.db.clear_embeddings()
        saved_count = 0
        people_count = 0

        for person_name in sorted(os.listdir(face_data_dir)):
            person_path = os.path.join(face_data_dir, person_name)
            if not os.path.isdir(person_path):
                continue

            student_id = self.db.upsert_student(person_name)
            people_count += 1
            image_names = [
                image_name
                for image_name in sorted(os.listdir(person_path))
                if image_name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
            ]
            print(f"Processing {person_name}: {len(image_names)} images")

            for index, image_name in enumerate(image_names, start=1):
                image_path = os.path.join(person_path, image_name)
                image = cv2.imread(image_path)
                if image is None:
                    continue

                embedding, quality_score = self._embedding_from_image(image)
                if embedding is None:
                    print(f"Skipped {image_path}: no face detected")
                    continue

                self.db.add_embedding(
                    student_id,
                    embedding,
                    image_path=image_path,
                    model_name=self.model_name,
                    quality_score=quality_score,
                )
                saved_count += 1

                if index % 10 == 0 or index == len(image_names):
                    print(f"  {person_name}: {index}/{len(image_names)} images registered")

        self.load_model()
        return people_count, saved_count

    def recognize_face(self, face_image):
        """
        Recognize a single image and return (student_id, cosine_distance).

        Lower distance means a better match. Unknown faces return (-1, 1.0).
        """
        embedding, _quality_score = self._embedding_from_image(face_image)
        if embedding is None:
            return -1, 1.0

        match = self._match_embedding(embedding)
        if match is None:
            return -1, 1.0

        return match["student_id"], match["distance"]

    def recognize_frame(self, frame):
        """Detect and recognize all faces in a full BGR frame."""
        results = []
        faces = self.detect_faces(frame)

        for face in faces:
            embedding = self._normalized_embedding(face)
            match = self._match_embedding(embedding)
            x1, y1, x2, y2 = self._bbox_to_int(face.bbox, frame.shape)

            if match:
                student_id = match["student_id"]
                name = match["student_name"]
                distance = match["distance"]
                similarity = match["similarity"]
            else:
                student_id = -1
                name = "Unknown"
                distance = 1.0
                similarity = 0.0

            results.append(
                {
                    "student_id": student_id,
                    "name": name,
                    "confidence": distance,
                    "similarity": similarity,
                    "is_known": self.is_known_person(distance),
                    "bbox": (x1, y1, x2 - x1, y2 - y1),
                    "crop": frame[y1:y2, x1:x2],
                    "det_score": float(getattr(face, "det_score", 0.0)),
                }
            )

        return results

    def get_person_name(self, label):
        return self.reverse_labels.get(label, "Unknown")

    def is_known_person(self, confidence):
        return confidence <= RECOGNITION_THRESHOLD

    def _embedding_from_image(self, image):
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        faces = self.detect_faces(image)
        if not faces:
            embedding = self._embedding_from_aligned_crop(image)
            if embedding is None:
                return None, None
            return embedding, 0.0

        face = max(faces, key=lambda item: self._bbox_area(item.bbox))
        return self._normalized_embedding(face), float(getattr(face, "det_score", 0.0))

    def _embedding_from_aligned_crop(self, image):
        """
        Fallback for legacy Haar/LBPH datasets where saved files are already
        tight face crops and InsightFace's detector cannot re-detect the face.
        """
        recognition_model = self.app.models.get("recognition")
        if recognition_model is None:
            return None

        input_width, input_height = recognition_model.input_size
        aligned = cv2.resize(image, (input_width, input_height))
        embedding = recognition_model.get_feat(aligned).flatten()
        norm = np.linalg.norm(embedding)
        if norm <= 0:
            return None
        return np.asarray(embedding / norm, dtype=np.float32)

    def _match_embedding(self, embedding):
        if not self.known_embeddings:
            return None

        best_match = None
        best_similarity = -1.0

        for known in self.known_embeddings:
            similarity = float(np.dot(embedding, known["embedding"]))
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = known

        distance = 1.0 - best_similarity
        if distance > RECOGNITION_THRESHOLD:
            return None

        return {
            "student_id": best_match["student_id"],
            "student_name": best_match["student_name"],
            "similarity": best_similarity,
            "distance": distance,
        }

    @staticmethod
    def _normalized_embedding(face):
        embedding = getattr(face, "normed_embedding", None)
        if embedding is None:
            embedding = face.embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
        return np.asarray(embedding, dtype=np.float32)

    @staticmethod
    def _bbox_area(bbox):
        x1, y1, x2, y2 = bbox
        return max(0, x2 - x1) * max(0, y2 - y1)

    @staticmethod
    def _bbox_to_int(bbox, image_shape):
        height, width = image_shape[:2]
        x1, y1, x2, y2 = bbox.astype(int)
        x1 = max(0, min(width - 1, x1))
        y1 = max(0, min(height - 1, y1))
        x2 = max(x1 + 1, min(width, x2))
        y2 = max(y1 + 1, min(height, y2))
        return x1, y1, x2, y2

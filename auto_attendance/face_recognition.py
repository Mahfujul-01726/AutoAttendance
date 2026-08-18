import logging
import os
import warnings
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from .config import (
    DATABASE_PATH,
    FACE_DATA_DIR,
    INSIGHTFACE_DET_SIZE,
    INSIGHTFACE_MAX_FACES,
    INSIGHTFACE_MODEL_NAME,
    INSIGHTFACE_PROVIDERS,
    RECOGNITION_THRESHOLD,
    UG_ADAPT_ENABLED,
)
from .database import AttendanceDatabase
from .quality_gate import QualityGate
from .template_adapter import DualMemoryTemplateAdapter
from .anti_spoofing import AntiSpoofing
from .cancelable_biometrics import CancelableBiometricsEngine
from .photometric_harmonization import AdaptiveRetinexHarmonizer
from .occlusion_gating import OcclusionAwareSubEmbeddingGater
from .homography_flow_guard import PlanarHomographyFlowGuard
from .explainable_ai import ExplainableSaliencyAttributor
from .rppg_pulse_guard import RemotePulseLivenessGuard
from .differential_privacy import HypersphericalDifferentialPrivacyEngine
from .adversarial_patch_filter import AdversarialPatchDefenseFilter
from .optimal_transport_aligner import CrossCameraOptimalTransportAligner
from .fairness_calibrator import DemographicFairnessCalibrator

warnings.filterwarnings(
    "ignore",
    message="`estimate` is deprecated.*",
    category=FutureWarning,
    module="insightface.utils.face_align",
)

logger = logging.getLogger(__name__)


class FaceRecognitionModule:
    """
    Face detection and recognition using InsightFace ArcFace embeddings,
    integrated with UG-Adapt Tri-Modal Quality Gate & Dual-Memory Adaptation.
    """

    def __init__(self, db_path=DATABASE_PATH, ug_adapt_enabled=UG_ADAPT_ENABLED):
        self.db = AttendanceDatabase(db_path)
        self.model_name = INSIGHTFACE_MODEL_NAME
        self.app = self._load_insightface()
        self.known_embeddings = []
        self.labels = {}
        self.reverse_labels = {}
        self.label_count = 0
        
        # UG-Adapt Comprehensive Research Engine Ecosystem
        self.ug_adapt_enabled = ug_adapt_enabled
        self.quality_gate = QualityGate()
        self.adapter = DualMemoryTemplateAdapter()
        self.anti_spoofing = AntiSpoofing()
        self.photometric_harmonizer = AdaptiveRetinexHarmonizer()
        self.cancelable_engine = CancelableBiometricsEngine()
        self.occlusion_gater = OcclusionAwareSubEmbeddingGater()
        self.flow_guard = PlanarHomographyFlowGuard()
        self.xai_attributor = ExplainableSaliencyAttributor()
        self.rppg_guard = RemotePulseLivenessGuard()
        self.dp_engine = HypersphericalDifferentialPrivacyEngine()
        self.patch_filter = AdversarialPatchDefenseFilter()
        self.ot_aligner = CrossCameraOptimalTransportAligner()
        self.fairness_calibrator = DemographicFairnessCalibrator()

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
            logger.info("No face embeddings found. Register faces first.")
            return

        logger.info(f"Loaded {len(self.known_embeddings)} face embeddings from {self.db.db_path}")

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
        """Register embeddings from existing face images."""
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
                continue

            self.db.add_embedding(
                student_id,
                embedding,
                model_name=self.model_name,
                quality_score=quality_score,
            )
            saved_count += 1

        self.load_model()
        logger.info(f"Registered {saved_count} embeddings in {self.db.db_path}")

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

            for index, image_name in enumerate(image_names, start=1):
                image_path = os.path.join(person_path, image_name)
                image = cv2.imread(image_path)
                if image is None:
                    continue

                embedding, quality_score = self._embedding_from_image(image)
                if embedding is None:
                    continue

                self.db.add_embedding(
                    student_id,
                    embedding,
                    image_path=image_path,
                    model_name=self.model_name,
                    quality_score=quality_score,
                )
                saved_count += 1

        self.load_model()
        return people_count, saved_count

    def train_on_faces(self, person_name: str, face_data_dir=FACE_DATA_DIR):
        """Train and register embeddings for a specific person or directory."""
        from pathlib import Path
        person_path = Path(face_data_dir) / person_name
        if not person_path.exists() or not person_path.is_dir():
            return self.train_from_directory(face_data_dir)

        student_id = self.db.upsert_student(person_name)
        with self.db._connect() as conn:
            conn.execute("DELETE FROM face_embeddings WHERE student_id = ?", (student_id,))

        image_files = [
            f for f in person_path.iterdir()
            if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp')
        ]

        saved_count = 0
        for img_path in image_files:
            image = cv2.imread(str(img_path))
            if image is None:
                continue

            embedding, quality_score = self._embedding_from_image(image)
            if embedding is None:
                continue

            self.db.add_embedding(
                student_id,
                embedding,
                image_path=str(img_path),
                model_name=self.model_name,
                quality_score=quality_score,
            )
            saved_count += 1

        self.load_model()
        logger.info(f"Registered {saved_count} embeddings for {person_name}")
        return saved_count

    def recognize_face(self, face_image):
        """Recognize a single image and return (student_id, cosine_distance)."""
        embedding, _quality_score = self._embedding_from_image(face_image)
        if embedding is None:
            return -1, 1.0

        match = self._match_embedding(embedding)
        if match is None:
            return -1, 1.0

        return match["student_id"], match["distance"]

    def recognize_frame(self, frame, liveness_scores: Optional[List[float]] = None):
        """
        Detect, recognize, and conditionally adapt faces in a full BGR frame.
        """
        results = []
        faces = self.detect_faces(frame)

        for idx, face in enumerate(faces):
            embedding = self._normalized_embedding(face)
            match = self._match_embedding(embedding)
            x1, y1, x2, y2 = self._bbox_to_int(face.bbox, frame.shape)
            crop = frame[y1:y2, x1:x2]
            landmarks = getattr(face, "kps", None)

            if liveness_scores and idx < len(liveness_scores):
                liveness = liveness_scores[idx]
            elif crop.size > 0:
                _is_live, liveness, _live_meta = self.anti_spoofing.evaluate_spatio_temporal_liveness(
                    face_crop=crop,
                    landmarks=landmarks,
                    subject_key=str(match["student_id"] if match else f"face_{idx}")
                )
            else:
                liveness = 1.0

            if match:
                student_id = match["student_id"]
                name = match["student_name"]
                distance = match["distance"]
                similarity = match["similarity"]
                
                # Check UG-Adapt Online Adaptation Hook
                adaptation_status = "BYPASSED"
                if self.ug_adapt_enabled and student_id > 0 and crop.size > 0:
                    adaptation_status, _adapt_metrics = self.adapt_template(
                        student_id=student_id,
                        student_name=name,
                        live_embedding=embedding,
                        face_crop=crop,
                        landmarks=landmarks,
                        liveness_score=liveness
                    )
            else:
                student_id = -1
                name = "Unknown"
                distance = 1.0
                similarity = 0.0
                adaptation_status = "NONE"

            results.append(
                {
                    "student_id": student_id,
                    "name": name,
                    "confidence": distance,
                    "similarity": similarity,
                    "is_known": self.is_known_person(distance),
                    "bbox": (x1, y1, x2 - x1, y2 - y1),
                    "crop": crop,
                    "landmarks": landmarks,
                    "det_score": float(getattr(face, "det_score", 0.0)),
                    "adaptation_status": adaptation_status,
                }
            )

        return results

    def adapt_template(
        self,
        student_id: int,
        student_name: str,
        live_embedding: np.ndarray,
        face_crop: np.ndarray,
        landmarks: Optional[np.ndarray] = None,
        liveness_score: float = 1.0
    ) -> Tuple[str, Dict[str, float]]:
        """
        Execute Quality Gate and Dynamic Adaptation for a recognized student.
        """
        # Find registered record
        record = next((item for item in self.known_embeddings if item["student_id"] == student_id), None)
        if not record:
            return "NO_RECORD", {}

        # 1. Evaluate Reliability Gate
        gate_passed, q_face, gate_metrics = self.quality_gate.evaluate(
            face_crop=face_crop,
            landmarks=landmarks,
            liveness_score=liveness_score,
            student_id=student_id
        )

        if not gate_passed:
            return "GATE_FAILED", gate_metrics

        # 2. Execute Dual-Memory Adaptation
        ltm = record["ltm_anchor"]
        stm = record["stm_prototype"]
        
        new_stm, status, adapt_metrics = self.adapter.adapt(
            live_embedding=live_embedding,
            ltm_anchor=ltm,
            current_stm=stm,
            quality_score=q_face,
            liveness_score=liveness_score,
            adaptation_count=record.get("adaptation_count", 0)
        )

        # 3. Persist to DB and update memory cache
        is_rollback = (status == "ROLLBACK")
        drift = adapt_metrics["drift_distance"]
        alpha = adapt_metrics["alpha"]

        self.db.update_stm_embedding(
            embedding_id=record["id"],
            new_stm_vector=new_stm,
            drift_score=drift,
            is_rollback=is_rollback
        )

        self.db.log_adaptation_event(
            student_id=student_id,
            student_name=student_name,
            alpha=alpha,
            quality_score=q_face,
            liveness_score=liveness_score,
            drift_score=drift,
            status=status
        )

        # Update in-memory reference
        record["stm_prototype"] = new_stm
        record["embedding"] = new_stm

        return status, {**gate_metrics, **adapt_metrics}

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
            ltm = known.get("ltm_anchor", known["embedding"])
            stm = known.get("stm_prototype", known["embedding"])

            # Dual-Memory joint similarity calculation
            joint_sim, _ltm_sim, _stm_sim = self.adapter.compute_joint_similarity(
                live_embedding=embedding,
                ltm_anchor=ltm,
                stm_prototype=stm
            )

            if joint_sim > best_similarity:
                best_similarity = joint_sim
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

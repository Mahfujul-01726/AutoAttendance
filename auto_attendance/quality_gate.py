"""
Quality Gate Module for UG-Adapt
Evaluates Geometric-Photometric Face Quality (GFQ) and Spatio-Temporal Consensus.
"""

import collections
import logging
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from .config import (
    UG_LIVENESS_THRESHOLD,
    UG_QUALITY_THRESHOLD,
    UG_TEMPORAL_WINDOW,
)

logger = logging.getLogger(__name__)


class QualityGate:
    """
    Tri-Modal Quality Gate for Safe Biometric Template Updates.
    
    Filters frames based on:
    1. Spatial sharpness (Laplacian variance)
    2. Illumination & brightness entropy
    3. 3D Head-Pose deviation (Yaw, Pitch)
    4. Multi-frame temporal consensus (FIFO Queue)
    """

    def __init__(
        self,
        quality_threshold: float = UG_QUALITY_THRESHOLD,
        liveness_threshold: float = UG_LIVENESS_THRESHOLD,
        temporal_window: int = UG_TEMPORAL_WINDOW,
        w_sharpness: float = 0.40,
        w_illumination: float = 0.30,
        w_pose: float = 0.30,
    ):
        self.quality_threshold = quality_threshold
        self.liveness_threshold = liveness_threshold
        self.temporal_window = temporal_window
        self.w_sharpness = w_sharpness
        self.w_illumination = w_illumination
        self.w_pose = w_pose

        # FIFO queues for temporal consensus: key = student_id, value = deque of recent detections
        self.temporal_buffers = collections.defaultdict(
            lambda: collections.deque(maxlen=self.temporal_window)
        )

    def calculate_sharpness(self, face_crop: np.ndarray) -> float:
        """Compute normalized Laplacian variance sharpness in [0.0, 1.0]."""
        if face_crop is None or face_crop.size == 0:
            return 0.0
        
        if len(face_crop.shape) == 3:
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_crop
            
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Normalize: Laplacian variance >= 300 is considered crystal clear (1.0)
        norm_sharpness = min(1.0, max(0.0, float(lap_var) / 300.0))
        return norm_sharpness

    def calculate_illumination(self, face_crop: np.ndarray) -> float:
        """Compute illumination score in [0.0, 1.0] (penalizes extreme shadows/glare)."""
        if face_crop is None or face_crop.size == 0:
            return 0.0
            
        if len(face_crop.shape) == 3:
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_crop
            
        mean_lum = np.mean(gray)
        # Optimal mean is ~128. Score degrades towards 0 (pitch dark) or 255 (overexposed)
        score = 1.0 - (abs(float(mean_lum) - 128.0) / 128.0)
        return max(0.0, min(1.0, score))

    def calculate_pose_score(self, landmarks: Optional[np.ndarray]) -> Tuple[float, float, float]:
        """
        Estimate Head Pose Quality in [0.0, 1.0] from 5 facial landmarks.
        Returns: (pose_score, estimated_yaw, estimated_pitch)
        """
        if landmarks is None or len(landmarks) < 5:
            # If no landmarks provided, assign neutral default score
            return 0.85, 0.0, 0.0

        pts = np.asarray(landmarks, dtype=np.float32)
        # Standard InsightFace 5 landmarks:
        # 0: left eye, 1: right eye, 2: nose tip, 3: left mouth corner, 4: right mouth corner
        left_eye = pts[0]
        right_eye = pts[1]
        nose = pts[2]
        left_mouth = pts[3]
        right_mouth = pts[4]

        # Horizontal symmetry (Yaw proxy)
        dist_left = np.linalg.norm(nose - left_eye)
        dist_right = np.linalg.norm(nose - right_eye)
        total_eye_dist = np.linalg.norm(right_eye - left_eye) + 1e-6

        yaw_ratio = abs(dist_left - dist_right) / total_eye_dist
        yaw_deg = float(yaw_ratio * 45.0)  # Approximate degrees

        # Vertical eye-nose vs nose-mouth ratio (Pitch proxy)
        eye_mid = (left_eye + right_eye) / 2.0
        mouth_mid = (left_mouth + right_mouth) / 2.0
        dist_eye_nose = np.linalg.norm(nose - eye_mid)
        dist_nose_mouth = np.linalg.norm(mouth_mid - nose) + 1e-6

        pitch_ratio = abs(dist_eye_nose - dist_nose_mouth) / (dist_eye_nose + dist_nose_mouth + 1e-6)
        pitch_deg = float(pitch_ratio * 30.0)

        # Pose Quality in [0, 1] with tolerance up to 30 deg
        pose_penalty = (yaw_deg + pitch_deg) / 40.0
        pose_score = max(0.0, min(1.0, 1.0 - pose_penalty))

        return pose_score, yaw_deg, pitch_deg

    def compute_disentangled_uncertainty(
        self,
        sharpness: float,
        illumination: float,
        pose_score: float,
        liveness_score: float = 1.0,
    ) -> Tuple[float, float, float]:
        """
        Decompose Epistemic vs. Aleatoric Evidential Uncertainty.
        
        Returns:
            (sigma_aleatoric_sq, sigma_epistemic_sq, sigma_total_sq)
        """
        # Aleatoric Uncertainty (Ambient / Sensor / Blur Noise)
        sigma_ale_sq = float(np.clip((1.0 - sharpness) * 0.55 + (1.0 - illumination) * 0.45, 0.0, 1.0))
        
        # Epistemic Uncertainty (Model Out-of-Distribution / Spoof / Extreme Pose)
        sigma_epi_sq = float(np.clip((1.0 - liveness_score) * 0.60 + (1.0 - pose_score) * 0.40, 0.0, 1.0))
        
        sigma_total_sq = float(np.clip(0.50 * sigma_ale_sq + 0.50 * sigma_epi_sq, 0.0, 1.0))
        return sigma_ale_sq, sigma_epi_sq, sigma_total_sq

    def evaluate_composite_quality(
        self,
        face_crop: np.ndarray,
        landmarks: Optional[np.ndarray] = None
    ) -> Tuple[float, Dict[str, float]]:
        """Compute composite Face Quality Score Q_face and Disentangled Uncertainty."""
        sharpness = self.calculate_sharpness(face_crop)
        illumination = self.calculate_illumination(face_crop)
        pose_score, yaw_deg, pitch_deg = self.calculate_pose_score(landmarks)

        q_face = (
            self.w_sharpness * sharpness
            + self.w_illumination * illumination
            + self.w_pose * pose_score
        )
        q_face = float(np.clip(q_face, 0.0, 1.0))

        ale_unc, epi_unc, tot_unc = self.compute_disentangled_uncertainty(
            sharpness=sharpness,
            illumination=illumination,
            pose_score=pose_score,
            liveness_score=1.0
        )

        metrics = {
            "sharpness": sharpness,
            "illumination": illumination,
            "pose_score": pose_score,
            "yaw_degrees": yaw_deg,
            "pitch_degrees": pitch_deg,
            "composite_quality": q_face,
            "aleatoric_uncertainty": ale_unc,
            "epistemic_uncertainty": epi_unc,
            "total_uncertainty": tot_unc,
        }
        return q_face, metrics

    def update_temporal_consensus(self, student_id: int, is_match: bool) -> bool:
        """
        Push match status to FIFO queue.
        Returns True if student is consistently detected across temporal window.
        """
        if student_id <= 0:
            return False
            
        buf = self.temporal_buffers[student_id]
        buf.append(is_match)
        
        # Buffer must be fully populated and all entries must be True
        if len(buf) == self.temporal_window and all(buf):
            return True
        return False

    def evaluate(
        self,
        face_crop: np.ndarray,
        landmarks: Optional[np.ndarray] = None,
        liveness_score: float = 1.0,
        student_id: Optional[int] = None,
    ) -> Tuple[bool, float, Dict[str, float]]:
        """
        Full gate check combining quality, anti-spoofing, and temporal consistency.
        
        Returns:
            (is_gate_passed, composite_quality, detailed_metrics)
        """
        q_face, metrics = self.evaluate_composite_quality(face_crop, landmarks)
        metrics["liveness_score"] = float(liveness_score)

        # 1. Quality Check
        quality_pass = q_face >= self.quality_threshold
        # 2. Liveness Check
        liveness_pass = liveness_score >= self.liveness_threshold
        # 3. Temporal Consensus Check
        temporal_pass = True
        if student_id is not None and student_id > 0:
            temporal_pass = self.update_temporal_consensus(student_id, is_match=True)
            metrics["temporal_consensus"] = 1.0 if temporal_pass else 0.0
        else:
            metrics["temporal_consensus"] = 0.0

        all_passed = quality_pass and liveness_pass and temporal_pass
        metrics["gate_passed"] = 1.0 if all_passed else 0.0

        return all_passed, q_face, metrics

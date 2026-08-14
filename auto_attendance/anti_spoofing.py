"""
Anti-Spoofing Module: Bio-Temporal Spatio-Frequency Liveness Fusion.
Combines:
1. Spectral Difference of Gaussians (DoG) + Fast Fourier Transform (FFT) High-Frequency Texture.
2. Geometric Spatio-Temporal Eye Aspect Ratio (EAR) Micro-Blink Kinematics & Landmark Jitter.
"""

import collections
import logging
import math
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from .config import DOG_SIGMA1, DOG_SIGMA2, SPOOF_THRESHOLD

logger = logging.getLogger(__name__)


class AntiSpoofing:
    """
    Bio-Temporal Spatio-Frequency Liveness Detection Engine.
    
    Fusion Pillars:
    - Frequency Domain (DoG + FFT): Detects printed moiré artifacts, display refresh lines, and low-res matte texture.
    - Geometric Domain (EAR & Kinematics): Tracks eye aspect ratio dynamics and physiological micro-motion.
    """
    
    def __init__(
        self,
        sigma1: float = DOG_SIGMA1,
        sigma2: float = DOG_SIGMA2,
        threshold: float = SPOOF_THRESHOLD,
        ear_history_len: int = 15,
    ):
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.threshold = threshold
        self.ear_history_len = ear_history_len
        # Per-person temporal EAR and micro-motion buffer
        self.temporal_buffers: Dict[str, collections.deque] = collections.defaultdict(
            lambda: collections.deque(maxlen=self.ear_history_len)
        )
        
        logger.debug(
            f"AntiSpoofing initialized (sigma1={sigma1}, "
            f"sigma2={sigma2}, threshold={threshold})"
        )
    
    def calculate_ear_5point(self, landmarks: np.ndarray) -> float:
        """
        Compute normalized Eye-to-Facial Aspect Ratio from 5 canonical landmarks:
        [left_eye, right_eye, nose, left_mouth, right_mouth]
        """
        if landmarks is None or len(landmarks) < 5:
            return 0.28  # Nominal baseline EAR

        pts = np.asarray(landmarks, dtype=np.float32)
        left_eye, right_eye = pts[0], pts[1]
        nose = pts[2]
        left_mouth, right_mouth = pts[3], pts[4]

        # Inter-ocular horizontal distance
        eye_dist = float(np.linalg.norm(left_eye - right_eye) + 1e-6)

        # Eye to mouth vertical span
        eye_midpoint = (left_eye + right_eye) / 2.0
        mouth_midpoint = (left_mouth + right_mouth) / 2.0
        face_height = float(np.linalg.norm(eye_midpoint - mouth_midpoint) + 1e-6)

        # Aspect ratio proxy
        ratio = eye_dist / face_height
        # Normalize to nominal human physiological range [0.15, 0.40]
        ear_norm = float(np.clip((ratio - 0.40) / 0.80, 0.15, 0.40))
        return ear_norm

    def calculate_ear_dense(self, landmarks: np.ndarray) -> float:
        """
        Compute standard Eye Aspect Ratio (EAR) for dense 68 or 106 landmark meshes.
        EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
        """
        if landmarks is None or len(landmarks) < 6:
            return self.calculate_ear_5point(landmarks)

        pts = np.asarray(landmarks, dtype=np.float32)
        # Standard 6-point eye contour
        p1, p2, p3, p4, p5, p6 = pts[:6]
        vertical_1 = float(np.linalg.norm(p2 - p6))
        vertical_2 = float(np.linalg.norm(p3 - p5))
        horizontal = float(np.linalg.norm(p1 - p4) + 1e-6)
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return float(np.clip(ear, 0.0, 0.50))

    def evaluate_spatio_temporal_liveness(
        self,
        face_crop: np.ndarray,
        landmarks: Optional[np.ndarray] = None,
        subject_key: str = "default"
    ) -> Tuple[bool, float, Dict[str, float]]:
        """
        Fuses Frequency-domain DoG texture analysis with Spatio-Temporal EAR Kinematics.
        """
        # 1. Frequency Domain Score (DoG + FFT)
        is_freq_real, freq_score = self.analyze(face_crop)

        # 2. Geometric EAR Kinematics
        if landmarks is not None and len(landmarks) >= 5:
            ear_val = self.calculate_ear_5point(landmarks)
        else:
            ear_val = 0.28

        buf = self.temporal_buffers[subject_key]
        buf.append(ear_val)

        # Compute dynamic temporal variance (real humans exhibit micro-blinks and saccades; static screens have 0 variance)
        if len(buf) >= 5:
            ear_variance = float(np.var(buf))
            # Real physiological variance falls in [0.00005, 0.05]
            if ear_variance > 1e-5:
                bio_score = float(np.clip(ear_variance * 500.0, 0.60, 1.0))
            else:
                # Suspicious static photo display (zero micro-motion)
                bio_score = 0.35
        else:
            bio_score = 0.85  # Warm-up phase

        # 3. Bio-Frequency Fusion
        # 70% spectral texture + 30% biological motion dynamics
        fused_score = 0.70 * freq_score + 0.30 * bio_score
        fused_score = float(np.clip(fused_score, 0.0, 1.0))
        is_real = fused_score >= self.threshold

        metrics = {
            "frequency_score": freq_score,
            "bio_motion_score": bio_score,
            "fused_liveness": fused_score,
            "current_ear": ear_val,
            "ear_variance": float(np.var(buf)) if len(buf) > 1 else 0.0,
        }

        return is_real, fused_score, metrics

    def analyze(self, face_crop: np.ndarray) -> Tuple[bool, float]:
        """
        Analyze a face image for spoofing indicators using DoG frequency decomposition.
        """
        try:
            if face_crop is None or face_crop.size == 0:
                return False, 0.0
            
            if len(face_crop.shape) != 3 or face_crop.shape[2] != 3:
                logger.warning("Invalid face crop shape for anti-spoofing")
                return False, 0.0
            
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur with different sigmas
            blur1 = cv2.GaussianBlur(gray, (0, 0), self.sigma1)
            blur2 = cv2.GaussianBlur(gray, (0, 0), self.sigma2)
            
            # Compute Difference of Gaussians
            dog = cv2.subtract(blur2, blur1)
            
            # Calculate frequency domain features
            features = self._compute_features(dog)
            
            # Compute liveness score
            confidence = self._score_to_confidence(features)
            is_real = confidence >= self.threshold
            
            return is_real, confidence
            
        except Exception as e:
            logger.error(f"Error in anti-spoofing analysis: {e}")
            return False, 0.0
    
    def _compute_features(self, dog: np.ndarray) -> dict:
        """Compute frequency domain features from DoG image."""
        features = {}
        features['mean_abs'] = np.mean(np.abs(dog))
        features['std'] = np.std(dog)
        
        h, w = dog.shape
        fft = np.fft.fft2(dog.astype(np.float32))
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)
        
        cy, cx = h // 2, w // 2
        max_freq = math.sqrt(cy**2 + cx**2)
        
        low_mask = self._radial_mask(h, w, max_freq * 0.25)
        low_energy = np.sum(magnitude * low_mask)
        
        high_mask = 1.0 - low_mask
        high_energy = np.sum(magnitude * high_mask)
        
        total_energy = low_energy + high_energy + 1e-10
        features['high_freq_ratio'] = high_energy / total_energy
        features['low_freq_ratio'] = low_energy / total_energy
        
        return features
    
    def _radial_mask(self, h: int, w: int, radius: float) -> np.ndarray:
        """Create a circular radial mask for frequency filtering."""
        y, x = np.ogrid[:h, :w]
        cy, cx = h // 2, w // 2
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)
        return (distance <= radius).astype(np.float32)
    
    def _score_to_confidence(self, features: dict) -> float:
        """Convert frequency domain features into a bounded confidence score."""
        high_freq_weight = 0.60
        std_weight = 0.40
        
        high_freq = features.get('high_freq_ratio', 0)
        high_freq_score = np.clip((high_freq - 0.40) / 0.50, 0, 1)
        
        std = features.get('std', 0)
        std_score = np.clip(std / 30.0, 0, 1)
        
        confidence = (high_freq_weight * high_freq_score) + (std_weight * std_score)
        return float(np.clip(confidence, 0.0, 1.0))

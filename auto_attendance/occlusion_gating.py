"""
Occlusion-Aware Dynamic Sub-Embedding Gating (OADM) Module.
Enables robust recognition and adaptation under masks, winter scarves, and sunglasses.
Decouples Upper (Eyes/Forehead), Mid (Nose), and Lower (Mouth/Chin) spatial zones.
"""

from typing import Dict, Optional, Tuple
import cv2
import numpy as np


class OcclusionAwareSubEmbeddingGater:
    """
    Spatial Visibility & Occlusion-Aware Feature Gating Engine.
    """

    def __init__(self, entropy_threshold: float = 3.5):
        self.entropy_threshold = entropy_threshold

    def calculate_region_entropy(self, patch: np.ndarray) -> float:
        """Compute Shannon texture entropy of an image patch."""
        if patch is None or patch.size == 0:
            return 0.0
        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY) if len(patch.shape) == 3 else patch
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        hist = hist / (np.sum(hist) + 1e-8)
        non_zero = hist[hist > 0]
        entropy = -float(np.sum(non_zero * np.log2(non_zero)))
        return entropy

    def evaluate_spatial_visibility(
        self,
        face_crop: np.ndarray,
        landmarks: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Compute visibility weights for Upper, Mid, and Lower facial zones in [0, 1].
        
        Returns:
            (visibility_weights_array, metrics_dict)
            visibility_weights: [w_upper, w_mid, w_lower] where sum(w) = 1.0
        """
        if face_crop is None or face_crop.size == 0:
            return np.array([0.34, 0.33, 0.33], dtype=np.float32), {}

        h, w = face_crop.shape[:2]
        h_third = max(1, h // 3)

        # Segment 3 spatial zones
        upper_zone = face_crop[0:h_third, :]
        mid_zone = face_crop[h_third:2*h_third, :]
        lower_zone = face_crop[2*h_third:h, :]

        # Texture entropy check (occlusions like masks or solid scarves have uniform texture / low entropy)
        e_upper = self.calculate_region_entropy(upper_zone)
        e_mid = self.calculate_region_entropy(mid_zone)
        e_lower = self.calculate_region_entropy(lower_zone)

        # Color variance check in lower zone (detect solid surgical mask / cloth)
        lower_std = float(np.std(lower_zone))
        is_mask_detected = lower_std < 18.0 or e_lower < self.entropy_threshold

        # Upper zone glasses check
        upper_std = float(np.std(upper_zone))
        is_dark_glasses = upper_std < 15.0

        v_upper = 0.40 if is_dark_glasses else 1.0
        v_mid = 1.0
        v_lower = 0.20 if is_mask_detected else 1.0

        raw_weights = np.array([v_upper, v_mid, v_lower], dtype=np.float32)
        norm_weights = raw_weights / np.sum(raw_weights)

        metrics = {
            "upper_visibility": float(v_upper),
            "mid_visibility": float(v_mid),
            "lower_visibility": float(v_lower),
            "mask_detected": 1.0 if is_mask_detected else 0.0,
            "glasses_detected": 1.0 if is_dark_glasses else 0.0,
            "lower_entropy": e_lower,
        }

        return norm_weights, metrics

    def modulate_similarity_under_occlusion(
        self,
        base_similarity: float,
        visibility_weights: np.ndarray,
    ) -> float:
        """
        Dynamically scale match similarity confidence based on visible facial area.
        Compensates for reduced facial surface area without false rejections.
        """
        total_visibility = float(np.sum(visibility_weights * np.array([1.0, 1.0, 1.0])))
        effective_sim = base_similarity * (0.85 + 0.15 * total_visibility)
        return float(np.clip(effective_sim, 0.0, 1.0))

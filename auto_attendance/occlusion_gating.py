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
        High-precision mask and occlusion detection that prevents false positives on
        natural bare faces, beards, and mustaches.
        
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

        # 1. HSV Color Analysis on Lower Facial Zone
        hsv_lower = cv2.cvtColor(lower_zone, cv2.COLOR_BGR2HSV)
        hue_l = hsv_lower[:, :, 0]
        sat_l = hsv_lower[:, :, 1]
        val_l = hsv_lower[:, :, 2]

        # Blue/Cyan surgical mask: Hue in [80, 145], Saturation > 35
        blue_pixels = (hue_l >= 80) & (hue_l <= 145) & (sat_l > 35) & (val_l > 40)
        is_blue_surgical = float(np.mean(blue_pixels)) > 0.25

        # Pure White Medical / N95 mask: Very low saturation (< 25) and high brightness (> 175) with smooth surface
        white_pixels = (sat_l < 25) & (val_l > 175)
        is_white_mask = (float(np.mean(white_pixels)) > 0.35) and (float(np.std(lower_zone)) < 24.0)

        # Solid Black / Dark Fabric mask: Pitch black (V < 40) across majority of lower face
        black_pixels = (val_l < 40)
        is_black_mask = (float(np.mean(black_pixels)) > 0.45) and (float(np.std(lower_zone)) < 18.0)

        # High-Saturation Colored Cloth Mask (Orange, Saffron, Red, Yellow, Green fabric)
        # Natural human skin has soft saturation (20-65). Fabric masks have vivid dye (Sat > 70)
        vivid_cloth_pixels = (sat_l > 70) & (val_l > 50)
        is_vivid_cloth_mask = float(np.mean(vivid_cloth_pixels)) > 0.28

        # 2. Mid-Face Mask Rim Boundary & Structural Gradient Contrast
        # A mask has a prominent horizontal edge where the cloth starts (30% to 65% of height)
        # and smooth fabric below with no fine facial features compared to eyes
        mid_strip = face_crop[int(h * 0.30):int(h * 0.65), :]
        if mid_strip.size > 0:
            gray_mid = cv2.cvtColor(mid_strip, cv2.COLOR_BGR2GRAY) if len(mid_strip.shape) == 3 else mid_strip
            sobel_y = np.abs(cv2.Sobel(gray_mid, cv2.CV_32F, 0, 1, ksize=3))
            row_mean_grad = np.mean(sobel_y, axis=1)
            peak_rim_strength = float(np.max(row_mean_grad)) if len(row_mean_grad) > 0 else 0.0
        else:
            peak_rim_strength = 0.0

        # Compare fine structural texture between upper (eyes) and lower (mouth/cloth)
        gray_upper = cv2.cvtColor(upper_zone, cv2.COLOR_BGR2GRAY) if len(upper_zone.shape) == 3 else upper_zone
        gray_lower = cv2.cvtColor(lower_zone, cv2.COLOR_BGR2GRAY) if len(lower_zone.shape) == 3 else lower_zone
        lap_upper = float(np.mean(np.abs(cv2.Laplacian(gray_upper, cv2.CV_32F))))
        lap_lower = float(np.mean(np.abs(cv2.Laplacian(gray_lower, cv2.CV_32F))))
        texture_ratio = lap_lower / (lap_upper + 1e-6)

        # Cloth mask/covering is detected if:
        # A strong rim boundary exists (> 8.5) and lower face has smooth cloth texture (ratio < 0.55)
        is_rim_cloth_occlusion = (peak_rim_strength > 8.5 and texture_ratio < 0.55)

        # 3. YCrCb Skin Chrominance on Upper vs Lower Face
        ycrcb_lower = cv2.cvtColor(lower_zone, cv2.COLOR_BGR2YCrCb)
        cr_l = ycrcb_lower[:, :, 1]
        cb_l = ycrcb_lower[:, :, 2]
        # Strict non-skin mask fabric (e.g. green, purple, blue, dark cloth)
        is_non_skin_lower = (cr_l < 118) | (cr_l > 185) | (cb_l < 70) | (cb_l > 135)
        is_colored_cloth_mask = float(np.mean(is_non_skin_lower)) > 0.45

        # 4. Check lip contrast in center mouth ROI
        mouth_center = face_crop[int(h * 0.65):int(h * 0.88), int(w * 0.30):int(w * 0.70)]
        if mouth_center.size > 0:
            mouth_ycrcb = cv2.cvtColor(mouth_center, cv2.COLOR_BGR2YCrCb)
            mouth_cr = mouth_ycrcb[:, :, 1]
            lip_contrast = float(np.max(mouth_cr) - np.min(mouth_cr))
        else:
            lip_contrast = 25.0

        e_lower = self.calculate_region_entropy(lower_zone)

        # Final Mask Decision
        is_mask_detected = bool(
            is_blue_surgical or
            is_white_mask or
            is_black_mask or
            is_vivid_cloth_mask or
            is_rim_cloth_occlusion or
            is_colored_cloth_mask
        )

        # 5. Dark Sunglasses in Upper Zone
        val_u = cv2.cvtColor(upper_zone, cv2.COLOR_BGR2HSV)[:, :, 2]
        is_dark_glasses = bool(float(np.mean(val_u < 35)) > 0.50)

        v_upper = 0.40 if is_dark_glasses else 1.0
        v_mid = 0.70 if is_mask_detected else 1.0
        v_lower = 0.15 if is_mask_detected else 1.0

        raw_weights = np.array([v_upper, v_mid, v_lower], dtype=np.float32)
        norm_weights = raw_weights / np.sum(raw_weights)

        metrics = {
            "upper_visibility": float(v_upper),
            "mid_visibility": float(v_mid),
            "lower_visibility": float(v_lower),
            "mask_detected": 1.0 if is_mask_detected else 0.0,
            "glasses_detected": 1.0 if is_dark_glasses else 0.0,
            "vivid_cloth": 1.0 if is_vivid_cloth_mask else 0.0,
            "rim_strength": round(peak_rim_strength, 1),
            "texture_ratio": round(texture_ratio, 2),
            "lower_entropy": round(e_lower, 2),
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

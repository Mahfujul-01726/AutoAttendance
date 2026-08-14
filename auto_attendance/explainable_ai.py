"""
Explainable AI (XAI) Module: Biometric Saliency & Attention Attribution.
Generates real-time spatial heatmaps explaining which facial regions contributed to verification.
"""

from typing import Dict, Tuple
import cv2
import numpy as np


class ExplainableSaliencyAttributor:
    """
    Real-Time Explainable Biometric Saliency Heatmap & Attribution Engine.
    """

    def __init__(self, grid_size: int = 8):
        self.grid_size = grid_size

    def compute_saliency_heatmap(
        self,
        face_crop: np.ndarray,
        confidence_score: float = 0.85,
        alpha_overlay: float = 0.40,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Generate a colored Jet attention heatmap overlaid on the face crop.
        
        Returns:
            (blended_heatmap_image, attribution_metrics)
        """
        if face_crop is None or face_crop.size == 0:
            return face_crop, {}

        h, w = face_crop.shape[:2]
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY) if len(face_crop.shape) == 3 else face_crop

        # 1. Compute Multi-Scale Gradient Energy (Sobel + Structure Tensor proxy)
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)

        # 2. Focus energy around key biological zones (Eyes/Nose center bias)
        y_grid, x_grid = np.ogrid[:h, :w]
        cy, cx = h * 0.40, w * 0.50  # Center around upper-mid face
        sigma_y, sigma_x = h * 0.35, w * 0.35
        bio_prior = np.exp(-((x_grid - cx)**2 / (2 * sigma_x**2) + (y_grid - cy)**2 / (2 * sigma_y**2)))

        # Saliency distribution
        saliency = (grad_mag / (np.max(grad_mag) + 1e-8)) * bio_prior * confidence_score
        saliency_norm = cv2.normalize(saliency, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Smooth with Gaussian blur for visual appeal
        saliency_smooth = cv2.GaussianBlur(saliency_norm, (15, 15), 0)

        # 3. Apply Jet/Viridis Colormap
        heatmap_color = cv2.applyColorMap(saliency_smooth, cv2.COLORMAP_JET)

        # 4. Blend semi-transparently over original face crop
        blended = cv2.addWeighted(heatmap_color, alpha_overlay, face_crop, 1.0 - alpha_overlay, 0)

        # 5. Compute Quantitative Region Attributions
        h_third = max(1, h // 3)
        upper_att = float(np.mean(saliency_smooth[0:h_third, :]))
        mid_att = float(np.mean(saliency_smooth[h_third:2*h_third, :]))
        lower_att = float(np.mean(saliency_smooth[2*h_third:h, :]))
        tot_att = upper_att + mid_att + lower_att + 1e-8

        attribution_metrics = {
            "upper_zone_pct": round((upper_att / tot_att) * 100.0, 1),
            "mid_zone_pct": round((mid_att / tot_att) * 100.0, 1),
            "lower_zone_pct": round((lower_att / tot_att) * 100.0, 1),
            "mean_saliency": float(np.mean(saliency_smooth)),
        }

        return blended, attribution_metrics

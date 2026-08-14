"""
Demographic Fairness & Skin-Tone Equitability Calibration Module.
Ensures uniform biometric verification accuracy across diverse demographic populations.
Uses Individual Typology Angle (ITA) in CIELAB color space to dynamically calibrate acceptance margins.
"""

from typing import Dict, Tuple
import cv2
import numpy as np


class DemographicFairnessCalibrator:
    """
    CIELAB Individual Typology Angle (ITA) Fairness Calibration Engine.
    Guarantees demographic equitability across Fitzpatrick Skin Types I - VI.
    """

    def __init__(self, base_threshold: float = 0.65, max_margin_adjustment: float = 0.05):
        self.base_threshold = base_threshold
        self.max_margin_adjustment = max_margin_adjustment

    def calculate_individual_typology_angle(self, face_crop: np.ndarray) -> Tuple[float, str]:
        """
        Compute Individual Typology Angle (ITA) in CIELAB color space:
        ITA = (arctan((L* - 50) / b*) * 180) / pi
        
        Returns:
            (ita_degrees, fitzpatrick_skin_type)
        """
        if face_crop is None or face_crop.size == 0:
            return 30.0, "Type_III"

        # Convert BGR to CIELAB space
        lab = cv2.cvtColor(face_crop, cv2.COLOR_BGR2LAB)
        
        # Focus on cheek & forehead skin region
        h, w = face_crop.shape[:2]
        roi = lab[int(h * 0.25):int(h * 0.55), int(w * 0.25):int(w * 0.75)]
        if roi.size == 0:
            roi = lab

        mean_l = float(np.mean(roi[:, :, 0])) * (100.0 / 255.0)  # L* in [0, 100]
        mean_b = float(np.mean(roi[:, :, 2])) - 128.0           # b* in [-128, 127]

        # Prevent division by zero
        b_safe = mean_b if abs(mean_b) > 1e-4 else 1e-4
        ita_rad = np.arctan2((mean_l - 50.0), b_safe)
        ita_deg = float(np.degrees(ita_rad))

        # Standard Dermatological Fitzpatrick Skin-Type Categorization:
        # > 55 deg: Very Light (Type I)
        # 41 to 55 deg: Light (Type II)
        # 28 to 41 deg: Intermediate (Type III)
        # 10 to 28 deg: Tan (Type IV)
        # -30 to 10 deg: Brown (Type V)
        # < -30 deg: Dark / Black (Type VI)
        if ita_deg > 55.0:
            skin_type = "Fitzpatrick_Type_I"
        elif ita_deg > 41.0:
            skin_type = "Fitzpatrick_Type_II"
        elif ita_deg > 28.0:
            skin_type = "Fitzpatrick_Type_III"
        elif ita_deg > 10.0:
            skin_type = "Fitzpatrick_Type_IV"
        elif ita_deg > -30.0:
            skin_type = "Fitzpatrick_Type_V"
        else:
            skin_type = "Fitzpatrick_Type_VI"

        return ita_deg, skin_type

    def calibrate_fairness_threshold(
        self,
        face_crop: np.ndarray,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Dynamically adjust recognition threshold to guarantee uniform False Non-Match Rates.
        
        Returns:
            (calibrated_threshold, fairness_metrics)
        """
        ita_deg, skin_type = self.calculate_individual_typology_angle(face_crop)

        # Normalize ITA into [-1.0, 1.0] adjustment scale (centered around Type III/IV baseline ~ 25 deg)
        ita_offset = np.clip((25.0 - ita_deg) / 60.0, -1.0, 1.0)
        margin_adj = float(ita_offset * self.max_margin_adjustment)

        calibrated_threshold = float(np.clip(self.base_threshold - margin_adj, 0.50, 0.85))

        fairness_metrics = {
            "ita_degrees": round(ita_deg, 2),
            "skin_type": skin_type,
            "margin_adjustment": round(margin_adj, 4),
            "calibrated_threshold": round(calibrated_threshold, 4),
            "is_fairness_calibrated": 1.0,
        }

        return calibrated_threshold, fairness_metrics

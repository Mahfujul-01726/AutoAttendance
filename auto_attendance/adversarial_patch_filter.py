"""
Adversarial Patch & AdvGlasses Defense Module.
Protects face recognition against physical adversarial stickers, printed glasses, and gradient attacks.
Uses Spatial Total Variation (TV) Gradient Regularization and Frequency Sparsification.
"""

from typing import Dict, Tuple
import cv2
import numpy as np


class AdversarialPatchDefenseFilter:
    """
    Physical Adversarial Noise & Eyeglass Patch Defense Engine.
    """

    def __init__(self, tv_weight: float = 0.15, gradient_threshold: float = 45.0):
        self.tv_weight = tv_weight
        self.gradient_threshold = gradient_threshold

    def detect_adversarial_gradients(self, face_crop: np.ndarray) -> Tuple[bool, float, Dict[str, float]]:
        """
        Detect artificial high-frequency adversarial perturbation energy.
        Adversarial patches have abnormally concentrated high-frequency gradient variance.
        """
        if face_crop is None or face_crop.size == 0:
            return False, 0.0, {}

        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY) if len(face_crop.shape) == 3 else face_crop
        
        # Compute Laplacian gradient energy
        laplacian = cv2.Laplacian(gray, cv2.CV_32F)
        lap_abs = np.abs(laplacian)
        
        # Local variance of gradient energy in 16x16 grid patches
        h, w = gray.shape
        patch_sz = max(8, min(h, w) // 6)
        
        max_local_energy = 0.0
        for y in range(0, h - patch_sz, patch_sz):
            for x in range(0, w - patch_sz, patch_sz):
                patch_energy = float(np.mean(lap_abs[y:y+patch_sz, x:x+patch_sz]))
                if patch_energy > max_local_energy:
                    max_local_energy = patch_energy

        mean_energy = float(np.mean(lap_abs) + 1e-6)
        energy_ratio = max_local_energy / mean_energy

        # An adversarial sticker causes sharp local energy peak (ratio > 4.5)
        is_adversarial_detected = (energy_ratio > 4.8) and (max_local_energy > self.gradient_threshold)

        metrics = {
            "max_local_energy": max_local_energy,
            "mean_energy": mean_energy,
            "energy_ratio": energy_ratio,
            "is_adversarial_patch": 1.0 if is_adversarial_detected else 0.0,
        }

        return is_adversarial_detected, energy_ratio, metrics

    def sanitize_adversarial_crop(self, face_crop: np.ndarray) -> np.ndarray:
        """
        Apply Total Variation (TV) bilateral denoising to strip adversarial noise.
        """
        if face_crop is None or face_crop.size == 0:
            return face_crop

        # Fast edge-preserving Bilateral Filter to strip adversarial high-frequency noise
        denoised = cv2.bilateralFilter(face_crop, d=7, sigmaColor=50, sigmaSpace=50)
        # Median filter to eliminate single-pixel adversarial perturbations
        median = cv2.medianBlur(denoised, 3)

        # Blend sanitized image
        sanitized = cv2.addWeighted(median, 0.85, face_crop, 0.15, 0)
        return sanitized

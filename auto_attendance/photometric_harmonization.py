"""
Adaptive Photometric Harmonization Module.
Implements Multi-Scale Retinex (MSR) and Dynamic Contrast Normalization for extreme lighting.
Solves cross-illumination, dynamic sunlight, and shadowed half-face classroom conditions.
"""

import cv2
import numpy as np


class AdaptiveRetinexHarmonizer:
    """
    Real-Time Illumination Equalization using Multi-Scale Retinex with Color Restoration (MSRCR).
    """

    def __init__(self, sigmas=(15, 80, 250)):
        self.sigmas = sigmas

    def single_scale_retinex(self, img_channel: np.ndarray, sigma: float) -> np.ndarray:
        """Compute Single-Scale Retinex: log(I) - log(I * G_sigma)."""
        img_float = img_channel.astype(np.float32) + 1.0
        blur = cv2.GaussianBlur(img_channel, (0, 0), sigma).astype(np.float32) + 1.0
        retinex = np.log10(img_float) - np.log10(blur)
        return retinex

    def multi_scale_retinex(self, img_channel: np.ndarray) -> np.ndarray:
        """Compute Multi-Scale Retinex across fine, medium, and coarse scales."""
        retinex = np.zeros_like(img_channel, dtype=np.float32)
        weight = 1.0 / len(self.sigmas)
        for sigma in self.sigmas:
            retinex += weight * self.single_scale_retinex(img_channel, sigma)
        return retinex

    def harmonize(self, face_crop: np.ndarray) -> np.ndarray:
        """
        Apply adaptive photometric illumination harmonization to a face crop.
        
        Args:
            face_crop: BGR face crop image (HxWx3)
            
        Returns:
            Harmonized BGR image with balanced illumination and enhanced texture.
        """
        if face_crop is None or face_crop.size == 0:
            return face_crop

        # 1. Convert to YCrCb space for luminance-chrominance decoupling
        ycrcb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2YCrCb)
        y_channel = ycrcb[:, :, 0]

        # 2. Compute Fast Multi-Scale Retinex on Luminance channel
        msr_y = self.multi_scale_retinex(y_channel)

        # 3. Dynamic Range Compression and Normalization
        mean = np.mean(msr_y)
        std = np.std(msr_y) + 1e-6
        min_val = mean - 2.0 * std
        max_val = mean + 2.0 * std
        norm_y = np.clip((msr_y - min_val) / (max_val - min_val) * 255.0, 0, 255).astype(np.uint8)

        # 4. Adaptive CLAHE touch for edge contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_y = clahe.apply(norm_y)

        # 5. Blend 70% enhanced luminance with 30% original for natural skin tone
        blended_y = cv2.addWeighted(enhanced_y, 0.70, y_channel, 0.30, 0)
        ycrcb[:, :, 0] = blended_y

        # 6. Convert back to BGR
        harmonized_bgr = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        return harmonized_bgr

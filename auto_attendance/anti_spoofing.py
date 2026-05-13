"""
Anti-Spoofing Module
Liveness detection using Difference of Gaussians (DoG) method.
Detects printed photos, screen replays, and other spoofing attempts.
"""

import logging
import math
from typing import Tuple, Optional

import cv2
import numpy as np

from .config import DOG_SIGMA1, DOG_SIGMA2, SPOOF_THRESHOLD

logger = logging.getLogger(__name__)


class AntiSpoofing:
    """
    Liveness detection using Difference of Gaussians (DoG).
    
    The DoG method exploits the fact that real faces have different
    frequency characteristics compared to printed photos or screens.
    Real faces exhibit higher frequency content than printed images.
    
    Detection Formula:
    - Compute DoG: smooth(image, sigma2) - smooth(image, sigma1)
    - Calculate variance in frequency bands
    - Compare to threshold to determine liveness
    """
    
    def __init__(
        self,
        sigma1: float = DOG_SIGMA1,
        sigma2: float = DOG_SIGMA2,
        threshold: float = SPOOF_THRESHOLD
    ):
        """
        Initialize anti-spoofing detector.
        
        Args:
            sigma1: Lower Gaussian blur sigma
            sigma2: Higher Gaussian blur sigma (sigma2 > sigma1)
            threshold: Spoof detection threshold (higher = more lenient)
        """
        self.sigma1 = sigma1
        self.sigma2 = sigma2
        self.threshold = threshold
        
        logger.debug(
            f"AntiSpoofing initialized (sigma1={sigma1}, "
            f"sigma2={sigma2}, threshold={threshold})"
        )
    
    def analyze(self, face_crop: np.ndarray) -> Tuple[bool, float]:
        """
        Analyze a face image for spoofing indicators.
        
        Args:
            face_crop: RGB face image (HxWx3)
            
        Returns:
            Tuple of (is_real, confidence_score)
            - is_real: True if genuine, False if spoof detected
            - confidence_score: 0-1 score where higher = more likely real
        """
        try:
            # Ensure valid input
            if face_crop is None or face_crop.size == 0:
                return False, 0.0
            
            if len(face_crop.shape) != 3 or face_crop.shape[2] != 3:
                logger.warning("Invalid face crop shape for anti-spoofing")
                return False, 0.0
            
            # Convert to grayscale for analysis
            if face_crop.shape[2] == 3:
                gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_crop[:, :, 0]
            
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
            
        except cv2.error as e:
            logger.error(f"OpenCV error in anti-spoofing: {e}")
            return False, 0.0
        except Exception as e:
            logger.error(f"Unexpected error in anti-spoofing: {e}", exc_info=True)
            return False, 0.0
    
    def _compute_features(self, dog: np.ndarray) -> dict:
        """
        Compute frequency domain features from DoG image.
        
        Args:
            dog: Difference of Gaussians image
            
        Returns:
            Dictionary of computed features
        """
        features = {}
        
        # Mean absolute value
        features['mean_abs'] = np.mean(np.abs(dog))
        
        # Standard deviation
        features['std'] = np.std(dog)
        
        # High frequency energy ratio using FFT
        h, w = dog.shape
        fft = np.fft.fft2(dog.astype(np.float32))
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)
        
        # Split into frequency bands
        cy, cx = h // 2, w // 2
        max_freq = math.sqrt(cy**2 + cx**2)
        
        # Low frequency region (center 25%)
        low_mask = self._radial_mask(h, w, max_freq * 0.25)
        low_energy = np.sum(magnitude * low_mask)
        
        # High frequency region (outer 75%)
        high_mask = 1 - low_mask
        high_energy = np.sum(magnitude * high_mask)
        
        total_energy = low_energy + high_energy + 1e-10
        
        features['high_freq_ratio'] = high_energy / total_energy
        features['low_freq_ratio'] = low_energy / total_energy
        
        return features
    
    def _radial_mask(self, h: int, w: int, radius: float) -> np.ndarray:
        """
        Create a circular mask for frequency filtering.
        
        Args:
            h: Image height
            w: Image width
            radius: Mask radius in pixels
            
        Returns:
            Binary mask (1 inside radius, 0 outside)
        """
        y, x = np.ogrid[:h, :w]
        cy, cx = h // 2, w // 2
        
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)
        mask = (distance <= radius).astype(np.float32)
        
        return mask
    
    def _score_to_confidence(self, features: dict) -> float:
        """
        Convert computed features to a confidence score.
        
        The confidence score reflects how likely the face is real
        based on frequency analysis. Real faces typically have
        higher high-frequency content than printed photos.
        
        Args:
            features: Computed frequency features
            
        Returns:
            Confidence score between 0 and 1
        """
        # Weights for different features
        high_freq_weight = 0.6
        std_weight = 0.4
        
        # Normalize high frequency ratio (typical range: 0.6-0.9 for real, 0.4-0.6 for spoof)
        high_freq = features.get('high_freq_ratio', 0)
        high_freq_score = np.clip((high_freq - 0.4) / 0.5, 0, 1)
        
        # Normalize standard deviation
        std = features.get('std', 0)
        std_score = np.clip(std / 30, 0, 1)  # Typical std range: 5-30
        
        # Combine scores
        confidence = (high_freq_weight * high_freq_score) + (std_weight * std_score)
        
        return float(np.clip(confidence, 0, 1))
    
    def batch_analyze(
        self,
        face_crops: list,
        min_confidence: float = 0.0
    ) -> list:
        """
        Analyze multiple face crops for spoofing.
        
        Args:
            face_crops: List of face images to analyze
            min_confidence: Minimum confidence to consider as real
            
        Returns:
            List of (is_real, confidence) tuples
        """
        results = []
        for crop in face_crops:
            is_real, confidence = self.analyze(crop)
            if confidence >= min_confidence:
                results.append((True, confidence))
            else:
                results.append((False, confidence))
        
        logger.debug(f"Batch analyzed {len(face_crops)} faces")
        return results
    
    def set_threshold(self, threshold: float) -> None:
        """
        Update the spoof detection threshold.
        
        Args:
            threshold: New threshold value (0-1)
        """
        self.threshold = float(np.clip(threshold, 0, 1))
        logger.info(f"Anti-spoofing threshold updated to {self.threshold}")
    
    def get_stats(self) -> dict:
        """
        Get current configuration statistics.
        
        Returns:
            Dictionary with current settings
        """
        return {
            'sigma1': self.sigma1,
            'sigma2': self.sigma2,
            'threshold': self.threshold,
            'method': 'DoG (Difference of Gaussians)'
        }

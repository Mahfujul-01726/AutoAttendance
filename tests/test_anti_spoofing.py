"""Unit tests for anti-spoofing module."""

import unittest
import numpy as np

from auto_attendance.anti_spoofing import AntiSpoofing


class TestAntiSpoofing(unittest.TestCase):
    """Test suite for AntiSpoofing module."""

    def test_module_initialization(self):
        """Test AntiSpoofing module initialization."""
        module = AntiSpoofing()
        self.assertIsNotNone(module)

    def test_analyze_valid_face(self):
        """Test analyzing a valid face image."""
        module = AntiSpoofing()
        face_crop = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        is_real, confidence = module.analyze(face_crop)
        
        self.assertIsInstance(is_real, bool)
        self.assertIsInstance(confidence, float)
        self.assertTrue(0.0 <= confidence <= 1.0)

    def test_analyze_invalid_shape(self):
        """Test handling of invalid image shape."""
        module = AntiSpoofing()
        face_crop = np.random.rand(112, 112).astype(np.uint8)
        is_real, confidence = module.analyze(face_crop)
        
        self.assertFalse(is_real)
        self.assertEqual(confidence, 0.0)

    def test_analyze_empty_image(self):
        """Test handling of empty image."""
        module = AntiSpoofing()
        is_real, confidence = module.analyze(None)
        
        self.assertFalse(is_real)
        self.assertEqual(confidence, 0.0)

    def test_spoof_detection_threshold(self):
        """Test that threshold is correctly applied."""
        module = AntiSpoofing(threshold=0.5)
        self.assertEqual(module.threshold, 0.5)


    def test_calculate_ear_5point(self):
        """Test 5-point landmark EAR calculation."""
        module = AntiSpoofing()
        # [left_eye, right_eye, nose, left_mouth, right_mouth]
        dummy_kps = np.array([
            [30, 40],
            [70, 40],
            [50, 60],
            [35, 80],
            [65, 80],
        ], dtype=np.float32)
        ear = module.calculate_ear_5point(dummy_kps)
        self.assertIsInstance(ear, float)
        self.assertTrue(0.10 <= ear <= 0.50)

    def test_evaluate_spatio_temporal_liveness(self):
        """Test fused spatio-temporal liveness evaluation."""
        module = AntiSpoofing()
        face_crop = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        dummy_kps = np.array([[30, 40], [70, 40], [50, 60], [35, 80], [65, 80]], dtype=np.float32)
        
        is_real, score, metrics = module.evaluate_spatio_temporal_liveness(
            face_crop=face_crop,
            landmarks=dummy_kps,
            subject_key="test_person"
        )
        self.assertIsInstance(is_real, bool)
        self.assertIsInstance(score, float)
        self.assertIn("bio_motion_score", metrics)
        self.assertIn("fused_liveness", metrics)


if __name__ == "__main__":
    unittest.main()
